'''
Created on 05-12-2010

@author: Xion

Module containing the Bot class, derived from IRCClient.
'''
from seejoo import ext, commands #@UnusedImport
from seejoo.config import config
from seejoo.util import irc
from seejoo.util.strings import normalize_whitespace
from twisted.internet import reactor, task
from twisted.internet.protocol import ReconnectingClientFactory
from twisted.words.protocols.irc import IRCClient
import functools
import logging
import os
import re


###############################################################################
# Bot class

# Regular expressions, compiled for speed
COMMAND_RE = re.compile(r"(?P<cmd>\w+)(\s+(?P<args>.+))?")

class Bot(IRCClient):
    ''' Main class of the bot, which is obviously an IRC client. '''
    versionName = 'seejoo'
    versionNum = '1.1'
    versionEnv = os.name
    
    def __init__(self, *args, **kwargs):
        ''' Initializer. '''
        self.nickname = config.nickname
        self.channels = set()
        
        self._register_meta_commands()    
        import seejoo.commands  # no longer dynamic

        self._import_plugins()
        self._init_plugins()

        # schedule a task to be ran every second
        tick_task = task.LoopingCall(self.tick)
        tick_task.start(1.0)

    def _register_meta_commands(self):
        ''' Registers the "meta" commands,
        i.e. those handled by the bot itself.
        '''
        for cmd, doc in ext.BOT_COMMANDS.iteritems():
            func = functools.partial(self._handle_command, cmd)
            func.__doc__ = doc
            ext.register_command(cmd, func)
    
    def _import_plugins(self):
        ''' Imports plugins listed in config.plugins.
        @return Number of plugins imported
        '''
        if not config.plugins:
            logging.info("No plugins to import.")
            return 0
        
        imported = 0
        for p in config.plugins:
            try:
                __import__(p, globals(), level = 0)
                logging.debug("Plugin '%s' imported successfully.", p)
                imported += 1
            except ImportError:
                logging.warning("Plugin '%s' could not be found.",
                                p, exc_info=True)
            except Exception, e:
                logging.warning("Could not import plugin '%s' (%s: %s).",
                                p, type(e).__name__, e)
        
        logging.info("Imported %s plugin(s)", imported)        
        return imported

    def _init_plugins(self):
        ''' Initializes plugins that have a configuration section in config.plugins. '''
        for plugin in ext._plugins:
            plugin_config = config.plugins.get(plugin.__module__)
            plugin(self, 'init', config=plugin_config)
        
    def _handle_command(self, cmd, args):
        ''' Handles a bot-level command. Returns its result. '''
        if cmd == 'help':
            
            if not args:
                return "No help found."
            
            doc = ext._get_command_doc(args)
            if doc:
                if config.cmd_prefix:
                    args = config.cmd_prefix + args
                doc = normalize_whitespace(doc)
                doc = doc.strip()
                return "%s -- %s" % (args, doc)
            else:
                return "No help found for '%s'" % args
    
    
    def tick(self):
        ''' Method called every second. Provides a way for plugins
        to perform actions based on time.
        '''
        ext.notify(self, 'tick')

    def signedOn(self):
        ''' Method called upon successful connection to IRC server. '''
        self.factory.resetDelay()
        logging.debug("[CONNECT] Connected to server")
        
        for chan in config.channels:
            self.join(chan)
        
        
    def myInfo(self, servername, version, umodes, cmodes):
        ''' Method called with information about the server. '''
        logging.debug("[SERVER] %s running %s; usermodes=%s, channelmodes=%s", servername, version, umodes, cmodes)
        ext.notify(self, 'connect', host = servername)

        
    def privmsg(self, user, channel, message):
        ''' Method called upon receiving a message on a channel or private message. '''
        if channel == "*":
            logging.debug("[SERVER] %s", message)
            return
        
        ext.notify(self, 'message',
                   user = user, channel = (channel if channel != self.nickname else None),
                   message = message, type = ext.MSG_SAY)
        
        is_priv = channel == self.nickname
        if is_priv:
            is_command = True   # on priv, everything's a command
            if config.cmd_prefix and message.startswith(config.cmd_prefix):
                message = message[len(config.cmd_prefix):]  # remove prefix if present anyway
        else:
            if config.cmd_prefix:
                is_command = message.startswith(config.cmd_prefix)
                if is_command:
                    message = message[len(config.cmd_prefix):]
            else:
                is_command = True   # if no prefix is defined, everything is a command
        
        logging.info ("[%s] <%s/%s> %s", "COMMAND" if is_command else "MESSAGE",
                       user, channel if not is_priv else '__priv__', message)
                       
        if is_command:
            resp = self._command(user, message)
            if resp:
                logging.info("[RESPONSE] %s", resp)
                irc.say(self, user if is_priv else channel, resp)
            
    def _command(self, user, command):
        ''' Internal function that handles the processing of commands. 
        Returns the result of processing as a text response to be "said" by the bot,
        or None if it wasn't actually a command.
        '''
        m = COMMAND_RE.match(command)
        if not m:   return
        
        cmd = m.group('cmd')
        args = m.groupdict().get('args')
        
        # Poll plugins for command result
        resp = ext.notify(self, 'command', user = user, cmd = cmd, args = args)
        if resp:    return resp
            
        # Plugins didn't care so find a command and invoke it if present
        cmd_object = ext.get_command(cmd)
        if cmd_object:
            if callable(cmd_object):    
                try:                    resp = cmd_object(args)
                except Exception, e:    resp = type(e).__name__ + ": " + str(e)
                resp = [resp] # Since we expect response to be iterable
            else:
                return ["Invalid command '%s'; likely indicates faulty plugin" % cmd]
        else:
            # Check whether the command can be unambiguously resolved
            completions = ext._commands.search(cmd).keys()
            if len(completions) == 1:
                command = completions[0]
                if args:    command += " %s" % args
                return self._command(user, command)
            
            # Otherwise, suggest other variants
            suggestions = set()
            for i in range(1, len(cmd) + 1):
                completions = ext._commands.search(cmd[:i]).keys()
                suggestions = suggestions.union(set(completions))
                
            if len(suggestions) == 0:
                resp = ["Unrecognized command '%s'." % cmd]
            else:
                # If there are too many suggestions, filter them out
                MAX_SUGGESTIONS = 5
                suggestions = filter(None, suggestions)
                more = None
                if len(suggestions) > MAX_SUGGESTIONS:
                    more = len(suggestions) - MAX_SUGGESTIONS
                    suggestions = suggestions[:MAX_SUGGESTIONS]
                
                # Format them
                if config.cmd_prefix:
                    suggestions = map(lambda s: config.cmd_prefix + s, suggestions)
                suggestions = str.join(" ", suggestions)
                if more:    suggestions += " ... (%s more)" % more
                
                resp = ["Did you mean one of: %s ?" % suggestions]
                    
        return resp
        
        
    def action(self, user, channel, message):
        ''' Method called when user performs and action (/me) in channel. '''
        is_priv = channel == self.nickname
        
        # Notify plugins and log message
        logging.debug("[ACTION] <%s/%s> %s", user, channel if not is_priv else '__priv__', message)
        ext.notify(self, 'message',
                   user = user, channel = (channel if not is_priv else None),
                   message = message, type = ext.MSG_ACTION)
        
    def noticed(self, user, channel, message):
        ''' Method called upon recieving notice message (either channel or private). '''
        is_priv = channel == self.nickname
        
        logging.debug("[NOTICE] <%s/%s> %s", user, channel if not is_priv else '__priv__', message)
        ext.notify(self, 'message',
                   user = user, channel = (channel if not is_priv else None),
                   message = message, type = ext.MSG_NOTICE)
        
    def modeChanged(self, user, channel, set, modes, args):
        ''' Method called when user changes mode(s) for a channel. '''
        logging.debug("[MODE] %s sets %s%s %s for %s", user, "+" if set else "-", modes, args, channel)
        ext.notify(self, 'mode',
                   user = user, channel = channel, set = set, modes = modes, args = args)
        
    def topicUpdated(self, user, channel, newTopic):
        ''' Method called when topic of channel changes or upon joining the channel. '''
        logging.debug("[TOPIC] <%s/%s> %s", user, channel, newTopic)
        ext.notify(self, 'topic', channel = channel, topic = newTopic, user = user)
        
    def joined(self, channel):
        ''' Method called when bot has joined a channel. '''
        self.channels.add(channel)
        logging.debug("[JOIN] %s to %s", self.nickname, channel)
        ext.notify(self, 'join', channel = channel, user = self.nickname)
        
    def userJoined(self, user, channel):
        ''' Method called when other user has joined a channel. '''
        logging.debug("[JOIN] %s to %s", user, channel)
        ext.notify(self, 'join', channel = channel, user = user)
        
    def left(self, channel):
        ''' Method called when bot has left a channel. '''
        self.channels.remove(channel)
        logging.debug("[PART] %s from %s", self.nickname, channel)
        ext.notify(self, 'part', user = self.nickname, channel = channel)
        
    def userLeft(self, user, channel):
        ''' Method called when other user has left a channel. '''
        logging.debug("[PART] %s from %s", self.nickname, channel)
        ext.notify(self, 'part', user = self.nickname, channel = channel)
        
    def kickedFrom(self, channel, kicker, message):
        ''' Method called when bot is kicked from a channel. '''
        self.channels.remove(channel)
        logging.debug("[KICK] %s from %s by %s (%s)", self.nickname, channel, kicker, message)
        ext.notify(self, 'kick', channel = channel, kicker = kicker, kickee = self.nickname, reason = message)
        
    def userKicked(self, kickee, channel, kicker, message):
        ''' Method called when other user is kicked from a channel. '''
        logging.debug("[KICK] %s from %s by %s (%s)", kickee, channel, kicker, message)
        ext.notify(self, 'kick', channel = channel, kicker = kicker, kickee = kickee, reason = message)
        
    def nickChanged(self, nick):
        ''' Method called when bot's nick has changed. '''
        old = self.nickname
        self.nickname = nick
        
        logging.debug("[NICK] %s -> %s", old, nick)
        ext.notify(self, 'nick', old = old, new = nick)
        
    def userRenamed(self, oldname, newname):
        ''' Method called when other user has changed their nick. '''
        logging.debug("[NICK] %s -> %s", oldname, newname)
        ext.notify(self, 'nick', old = oldname, new = newname)
        
    def userQuit(self, user, message):
        ''' Method called when other user has disconnected from IRC. '''
        logging.debug("[QUIT] %s (%s)", user, message)
        ext.notify(self, 'quit', user = user, message = message)


###############################################################################
# Runner

class BotFactory(ReconnectingClientFactory): 
    protocol = Bot

def run():
    ''' Runs the bot, using configuration specified in config module. '''
    reactor.connectTCP(config.server, config.port, BotFactory())    # @UndefinedVariable
    reactor.run()                                                   # @UndefinedVariable
