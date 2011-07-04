'''
Created on 05-12-2010

@author: Xion

Module containing the Bot class, derived from IRCClient.
'''
from seejoo import ext, commands #@UnusedImport
from seejoo.util import irc
from seejoo.config import config
from twisted.words.protocols.irc import IRCClient
import logging
import os
import re
from seejoo.util.common import normalize_whitespace
import functools


###############################################################################
# Bot class

# Regular expressions, compiled for speed
COMMAND_RE = re.compile(r"(?P<cmd>\w+)(\s+(?P<args>.+))?")

class Bot(IRCClient):
    
    versionName = 'seejoo'
    versionNum = '0.8'
    versionEnv = os.name
    
    def __init__(self, *args, **kwargs):
        ''' Initializer. '''
        self.nickname = config.nickname
        
        for cmd in ext.BOT_COMMANDS:
            ext.register_command(cmd, functools.partial(self._handle_command, cmd))
            
        self._import_plugins()
            
    def _import_plugins(self):
        '''
        Imports plugins listed in config.plugins.
        @return Number of plugins imported
        '''
        if not config.plugins:
            logging.info("No plugins to import.")
            return 0
        
        imported = 0
        for p in config.plugins:
            try:
                __import__(p, globals(), level = 0)
                logging.debug("Plugin '%s' imported successfully.")
                imported += 1
            except ImportError:
                logging.warning("Plugin '%s' could not be found.")
            except Exception, e:
                logging.warning("Could not import plugin '%s' (%s: %s).", p, type(e).__name__, e)
        
        logging.info("Imported %s plugin(s)", imported)        
        return imported
        
    def _handle_command(self, cmd, args):
        '''
        Handles a bot-level command. Returns its result.
        '''
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
    
    
    def signedOn(self):
        '''
        Method called upon successful connection to IRC server.
        '''
        self.factory.resetDelay()
        logging.debug("[CONNECT] Connected to server")
        
        # Join channels
        for chan in config.channels:    self.join(chan)
        
        
    def myInfo(self, servername, version, umodes, cmodes):
        '''
        Method called with information about the server.
        '''
        # Log and notify plugins
        logging.debug("[SERVER] %s running %s; usermodes=%s, channelmodes=%s", servername, version, umodes, cmodes)
        ext.notify(self, 'connect', host = servername)

        
    def privmsg(self, user, channel, message):
        '''
        Method called upon receiving a message on a channel or private message.
        '''
        # Discard server messages
        if channel == "*":  logging.debug("[SERVER] %s", message) ; return
        
        # Notify plugins
        ext.notify(self, 'message',
                   user = user, channel = (channel if channel != self.nickname else None),
                   message = message, type = ext.MSG_SAY)
        
        # First, check whether this is a private message and whether we shall interpret
        # it as a command invocation
        is_priv = channel == self.nickname
        if is_priv:
            is_command = True   # On priv, everything's a command
            if config.cmd_prefix and message.startswith(config.cmd_prefix): # Prefix is optional; get rid of it if present
                message = message[len(config.cmd_prefix):]
        else:
            if config.cmd_prefix:
                is_command = message.startswith(config.cmd_prefix)
                if is_command:  message = message[len(config.cmd_prefix):]  # Get rid of the prefix if present
            else:
                is_command = True   # If no prefix defined, everything is a command
        
        # Log message/command
        logging.info ("[%s] <%s/%s> %s", "COMMAND" if is_command else "MESSAGE",
                       user, channel if not is_priv else '__priv__', message)
        if is_command:
            resp = self._command(user, message)
            if resp:
                logging.info("[RESPONSE] %s", resp)
                irc.say(self, user if is_priv else channel, resp)
            
    def _command(self, user, command):
        '''
        Internal function that handles the processing of commands. 
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
            try:                    resp = cmd_object(args)
            except Exception, e:    resp = type(e).__name__ + ": " + str(e)
            resp = [resp] # Since we expect response to be iterable
        else:
            # Check whether the command can be unambiguously resolved
            completions = ext._commands.search(cmd).keys()
            if len(completions) == 1:
                command = "%s %s" % (completions[0], args)
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
        '''
        Method called when user performs and action (/me) in channel.
        '''
        is_priv = channel == self.nickname
        
        # Notify plugins and log message
        logging.debug("[ACTION] <%s/%s> %s", user, channel if not is_priv else '__priv__', message)
        ext.notify(self, 'message',
                   user = user, channel = (channel if not is_priv else None),
                   message = message, type = ext.MSG_ACTION)
        
    def noticed(self, user, channel, message):
        '''
        Method called upon recieving notice message (either channel or private).
        '''
        is_priv = channel == self.nickname
        
        # Notify plugins and log the message
        logging.debug("[NOTICE] <%s/%s> %s", user, channel if not is_priv else '__priv__', message)
        ext.notify(self, 'message',
                   user = user, channel = (channel if not is_priv else None),
                   message = message, type = ext.MSG_NOTICE)
        
    def modeChanged(self, user, channel, set, modes, args):
        '''
        Method called when user changes mode(s) for a channel.
        '''
        # Notify plugins and log the message
        logging.debug("[MODE] %s sets %s%s %s for %s", user, "+" if set else "-", modes, args, channel)
        ext.notify(self, 'mode',
                   user = user, channel = channel, set = set, modes = modes, args = args)
        
    def topicUpdated(self, user, channel, newTopic):
        '''
        Method called when topic of channel changes or upon joining the channel.
        '''
        # Notify plugins and log message
        logging.debug("[TOPIC] <%s/%s> %s", user, channel, newTopic)
        ext.notify(self, 'topic', channel = channel, topic = newTopic, user = user)
        
    def joined(self, channel):
        '''
        Method called when bot has joined a channel.
        '''
        # Notify plugins and log the event
        logging.debug("[JOIN] %s to %s", self.nickname, channel)
        ext.notify(self, 'join', channel = channel, user = self.nickname)
        
    def userJoined(self, user, channel):
        '''
        Method called when other user has joined a channel.
        '''
        # Notify plugins and log event
        logging.debug("[JOIN] %s to %s", user, channel)
        ext.notify(self, 'join', channel = channel, user = user)
        
    def left(self, channel):
        '''
        Method called when bot has left a channel.
        '''
        # Notify plugins and log event
        logging.debug("[PART] %s from %s", self.nickname, channel)
        ext.notify(self, 'part', user = self.nickname, channel = channel)
        
    def userLeft(self, user, channel):
        '''
        Method called when other user has left a channel.
        '''
        # Notify plugins and log event
        logging.debug("[PART] %s from %s", self.nickname, channel)
        ext.notify(self, 'part', user = self.nickname, channel = channel)
        
    def kickedFrom(self, channel, kicker, message):
        '''
        Method called when bot is kicked from a channel.
        '''
        # Notify plugins and log event
        logging.debug("[KICK] %s from %s by %s (%s)", self.nickname, channel, kicker, message)
        ext.notify(self, 'kick', channel = channel, kicker = kicker, kickee = self.nickname, reason = message)
        
    def userKicked(self, kickee, channel, kicker, message):
        '''
        Method called when other user is kicked from a channel.
        '''
        # Notify plugins and log event
        logging.debug("[KICK] %s from %s by %s (%s)", kickee, channel, kicker, message)
        ext.notify(self, 'kick', channel = channel, kicker = kicker, kickee = kickee, reason = message)
        
    def nickChanged(self, nick):
        '''
        Method called when bot's nick has changed.
        '''
        # Remember new nick
        old = self.nickname
        self.nickname = nick
        
        # Notify plugins and log event
        logging.debug("[NICK] %s -> %s", old, nick)
        ext.notify(self, 'nick', old = old, new = nick)
        
    def userRenamed(self, oldname, newname):
        '''
        Method called when other user has changed their nick.
        '''
        # Notify plugins and log event
        logging.debug("[NICK] %s -> %s", oldname, newname)
        ext.notify(self, 'nick', old = oldname, new = newname)
        
    def userQuit(self, user, message):
        '''
        Method called when other user has disconnected from IRC.
        '''
        # Notify plugins and log event
        logging.debug("[QUIT] %s (%s)", user, message)
        ext.notify(self, 'quit', user = user, message = message)
