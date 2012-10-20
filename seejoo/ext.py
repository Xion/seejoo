'''
Created on 2010-12-05

@author: xion

Extensions module. Contains installed commands and plugins, as well as functions
to register them. Shall be used by external modules to add extensions to seejoo.
'''
from seejoo.config import config
from seejoo.util.prefix_tree import PrefixTree
import functools
import logging
import os
import types
import collections


BOT_COMMANDS = {'help': 'Displays help about particular command'}

_commands = PrefixTree()
_plugins = []


def _get_command_doc(cmd_name):
    ''' Retrieves a documentation for particular command. '''
    if not cmd_name:
        return

    cmd_obj = _commands.get(cmd_name)
    if not cmd_obj:
        return

    # The command object is either a callable with command itself
    # or a documentation string
    if callable(cmd_obj):
        try:
            doc = cmd_obj.__doc__
        except AttributeError:
            return "<no description available>"
    else:
        doc = str(cmd_obj)

    # Perform substitition of #cmd#
    doc = doc.replace("#cmd#", config.cmd_prefix + cmd_name)
    return doc


# Commands

def register_command(name, cmd_object):
    ''' Registers a new command.

    Commands are bot's utility functions that can be
    invoked on IRC by saying their names and arguments on the channel where
    bot is present (following prefix defined in configuration) or by sending
    a private message to the bot (with or without prefix).

    :param name: A name of the command. This is also the phrase used to invoke it
    :param cmd_object: A callable object which performs the command's action.
                       It should accept a single argument which will be
                       a string containing command's invocation parameters,
                       as well as keywords arguments such as 'user'.
    '''
    global _commands

    if not name:
        logging.error('Command name must not be empty.')
        return
    if name in _commands:
        logging.error('Duplicate or reserved command name "%s"', name)
        return

    _commands.add(name, cmd_object)
    return cmd_object


def command(name):
    ''' Decorator functions for registering commands easily. '''
    return functools.partial(register_command, name)


def get_command(cmd):
    ''' Retrieves a command object associated with given name. '''
    global _commands
    return _commands.get(cmd)


# Plugins

def register_plugin(plugin):
    '''
    Registers a new plugin.

    Plugins are more complex utilities that can
    control bot's behavior in response to incoming events.

    A plugin is a callable that is invoked every time an IRC event occurs;
    it contains two required arguments (bot object & event type) and keyword arguments
    specific to particular event. It's return value is usually ignored, except
    for the 'command' event which - if not None - is taken as a result of the command
    and produced by bot instead of looking up a command and executing it.

    Plugins can also have a list of commands specified explicitly as their 'commands'
    attribute. This way the bot can offer help for the commands upon request.
    @param plugin: Plugin object
    '''
    if not callable(plugin):
        logging.error('Plugin object "%s" is not callable.', str(plugin))
        return

    # if plugin declares any commands, add them to command tree
    cmds = getattr(plugin, 'commands', None)
    if cmds:
        if isinstance(cmds, collections.Mapping):
            for k, v in cmds.iteritems():
                register_command(k, v)
        else:
            for cmd in cmds:
                register_command(str(cmd), None)

    global _plugins
    _plugins.append(plugin)


class Plugin(object):
    '''Base class that can be derived in by plugin objects.
    # It intercepts events and converts them to method calls.
    '''
    def init(self, bot, config):
        pass

    def connect(self, bot, host):
        pass

    def join(self, bot, channel, user):
        pass

    def part(self, bot, channel, user):
        pass

    def kick(self, bot, channel, kicker, kickee, reason):
        pass

    def quit(self, bot, user, message):
        pass

    def message(self, bot, channel, user, message, type):
        pass

    def nick(self, bot, old, new):
        pass

    def mode(self, bot, channel, user, set, modes, args):
        pass

    def topic(self, bot, channel, topic, user):
        pass

    def command(self, bot, channel, user, cmd, args):
        pass

    def tick(self, bot):
        pass

    def __call__(self, bot, event, **kwargs):
        try:
            return getattr(self, event)(bot, **kwargs)
        except AttributeError:
            pass  # Should not happen


def plugin(plugin):
    '''
    A decorator function for automatic registration of plugins. If used for functions,
    it registers them as plugins. If used for classes, it instantiates the class and
    uses it's object as a plugin.
    '''
    if isinstance(plugin, types.FunctionType):
        register_plugin(plugin)
    if isinstance(plugin, (types.ClassType, types.TypeType)):
        register_plugin(plugin())
    return plugin


def notify(bot, event, **kwargs):
    ''' Notifies all registered plugins about an IRC event. '''
    try:
        if event != 'command':
            for p in _plugins:
                p(bot, event, **kwargs)
        else:
            # Get command results, remove Nones
            # and turn whole result to None if nothing remains
            res = [p(bot, event, **kwargs) for p in _plugins]
            res = filter(lambda x: x is not None, res)
            if len(res) == 0:
                res = None

            return res

    except Exception, e:
        logging.exception("Error while notifying plugins: %s - %s",
                          type(e).__name__, e)


# Flags used by seejoo when notifying plugins
MSG_SAY = "say"
MSG_ACTION = "action"
MSG_NOTICE = "notice"


# API available for plugins

def get_storage_dir(plugin):
    '''
    Retrieves a path to a directory which can be used for storing
    local data, specific to a given plugin.
    '''
    if not plugin:
        return None

    data_dir = os.path.expanduser("~/.seejoo/data/plugins")

    # Form the name of directory
    name = None
    try:
        if isinstance(plugin, types.FunctionType):
            name = plugin.__name__
        else:
            name = plugin.__class__.__name__
        name = plugin.__module__ + '.' + name
    except AttributeError:
        pass
    if not name:
        return None

    # Make sure it exists
    dir = "%s/%s/" % (data_dir, name)
    if not os.path.exists(dir):
        os.makedirs(dir)

    return dir
