'''
Created on 2010-12-05

@author: xion

Extensions module. Contains installed commands and plugins, as well as functions
to register them. Shall be used by external modules to add extensions to seejoo.
'''
import logging
import functools
import types


###############################################################################
# Commands

_commands = {}

def register_command(name, cmd_object):
    '''
    Registers a new command. Commands are bot's utility functions that can be
    invoked on IRC by saying their names and arguments on the channel where
    bot is present (following prefix defined in configuration) or by sending
    a private message to the bot (with or without prefix).
    @param name: A name of the command. This is also the phrase used to invoke it
    @param cmd_object: A callable object which performs the command's action.
                       It should accept a single argument which will be
                       a string containing command's invocation parameters,
                       as well as keywords arguments such as 'user'.
    '''
    if not name or len(name) == 0:
        logging.error('Command name must not be empty.') ; return
    if name in _commands:
        logging.error('Duplicate command name "%s"', name) ; return
    if not callable(cmd_object):
        logging.error('Command object "%s" is not callable.', str(cmd_object)) ; return
        
    _commands[name] = cmd_object
    
    
def command(name):
    '''
    Decorator functions for registering commands easily.
    '''
    return functools.partial(register_command, name)


def get_command(cmd):
    '''
    Retrieves a command object associated with given name.
    '''
    global _commands
    return _commands.get(cmd)


###############################################################################
# Plugins

_plugins = []

def register_plugin(plugin):
    '''
    Registers a new plugin. Plugins are more complex utilities that can
    control bot's behavior in response to incoming events.
    A plugin is a callable that is invoked every time an IRC event occurs;
    it contains two required arguments (bot object & event type) and keyword arguments
    specific to particular event.
    @param plugin: Plugin object
    '''
    if not callable(plugin):
        logging.error('Plugin object "%s" is not callable.', str(plugin)) ; return
        
    _plugins.append(plugin)


class Plugin(object):
    '''
    Base class that can be derived in by plugin objects. It intercepts
    events and converts them to method calls.
    '''
    def connect(self, bot):                                 pass
    def join(self, bot, channel, user):                     pass
    def part(self, bot, channel, user):                     pass
    def kick(self, bot, channel, kicker, kickee, reason):   pass
    def quit(self, bot, user, message):                     pass
    def message(self, bot, channel, user, type):            pass
    def nick(self, bot, old, new):                          pass
    def mode(self, bot, channel, user, set, modes, args):   pass
    def topic(self, bot, channel, topic, user):             pass
    
    def __call__(self, bot, event, **kwargs):
        try:                    getattr(self, event)(bot, **kwargs)
        except AttributeError:  pass    # Should not happen
        
    
def plugin(plugin):
    '''
    A decorator function for automatic registration of plugins. If used for functions,
    it registers them as plugins. If used for classes, it instantiates the class and
    uses it's object as a plugin.
    '''
    t = type(plugin)
    if t == types.FunctionType:
        register_plugin(plugin)
    if t == types.ClassType or t == types.TypeType:
        register_plugin(plugin())


def notify(bot, event, **kwargs):
    '''
    Notifies all registered plugins about an IRC event.
    ''' 
    try:
        for p in _plugins:  p(bot, event, **kwargs)
    except Exception, e:
        pass
    
    
# Flags used by seejoo when notifying plugins
MSG_SAY = "say"
MSG_ACTION = "action"
MSG_NOTICE = "notice"