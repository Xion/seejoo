'''
Created on 05-12-2010

@author: Xion

Module containing the Bot class, derived from IRCClient.
'''
from seejoo import ext
from seejoo import commands                                 #@UnusedImport
from seejoo.config import config
from twisted.words.protocols.irc import IRCClient
import logging
import os
import re


# Regular expressions, compiled for speed
USER_RE = re.compile(r"(?P<nick>.*)\!(?P<id>.*)\@(?P<host>.*)")
COMMAND_RE = re.compile(r"(?P<cmd>\w+)(\s+(?P<args>.+))?")

# Limits for messages
LINE_MAX_LEN = 512
MESSAGE_MAX_LEN = 768


class Bot(IRCClient):
    
    versionName = 'seejoo'
    versionNum = '0.1'
    versionEnv = os.name
    
    def __init__(self, *args, **kwargs):
        self.nickname = config.nickname
    
    
    def signedOn(self):
        '''
        Method called upon successful connection to IRC server.
        '''
        self.factory.resetDelay()
        
        # Notify plugins and log event
        logging.debug("[CONNECT] Connected to server")
        ext.notify(self, 'connect')
        
        # Join channels
        for chan in config.channels:    self.join(chan)
    
        
    def privmsg(self, user, channel, message):
        '''
        Method called upon receiving a message on a channel or private message.
        '''
        # Notify plugins
        ext.notify(self, 'message',
                   user=user, channel=(channel if channel != self.nickname else None),
                   message=message, type=ext.MSG_SAY)
        
        # Discard server messages
        if channel == "*":  logging.debug("[SERVER] %s", message) ; return
        
        # First, check whether this is a private message and whether we shall interpret
        # it as a command invocation
        is_priv = channel == self.nickname
        if is_priv: is_command = True
        else:
            if config.cmd_prefix:
                is_command = message.startswith(config.cmd_prefix)
                if is_command:  message = message[len(config.cmd_prefix):]  # Get rid of the prefix if present
            else:
                is_command = True   # If no prefix defined, everything is a command
        
        # Log message/command
        logging.debug ("[%s] <%s/%s> %s", "COMMAND" if is_command else "MESSAGE",
                       user, channel if not is_priv else '__priv__', message)
        if not is_command: return
                
        # Split command to prefix and argument line
        m = COMMAND_RE.match(message)
        if m:
            cmd = m.group('cmd')
            args = m.groupdict().get('args')
            
            # Find a command and invoke it if present
            cmd_object = ext.get_command(cmd)
            if not cmd_object:  resp = "Unknown command '%s'." % cmd
            else:
                try:                    resp = unicode(cmd_object(args)).encode('utf-8', 'ignore')
                except Exception, e:    resp = type(e).__name__ + ": " + str(e)
            
        else:   resp = ""
        
        # Trim and serve the response
        resp = resp[:MESSAGE_MAX_LEN]
        if is_priv:
            
            # Retrieve the nick of user
            m = USER_RE.match(user)
            nick = m.groupdict().get('nick') if m else None
            
            self.msg(nick, resp, LINE_MAX_LEN)
            
        else:       self.say(channel, resp, LINE_MAX_LEN)
        logging.debug("[RESPONSE] %s", resp)
        
        
    def action(self, user, channel, message):
        '''
        Method called when user performs and action (/me) in channel.
        '''
        is_priv = channel == self.nickname
        
        # Notify plugins and log message
        logging.debug("[ACTION] <%s/%s> %s", user, channel if not is_priv else '__priv__', message)
        ext.notify(self, 'message',
                   user=user, channel=(channel if not is_priv else None),
                   message=message, type=ext.MSG_ACTION)
        
    def noticed(self, user, channel, message):
        '''
        Method called upon recieving notice message (either channel or private).
        '''
        is_priv = channel == self.nickname
        
        # Notify plugins and log the message
        logging.debug("[NOTICE] <%s/%s> %s", user, channel if not is_priv else '__priv__', message)
        ext.notify(self, 'message',
                   user=user, channel=(channel if not is_priv else None),
                   message=message, type=ext.MSG_NOTICE)
        
    def modeChanged(self, user, channel, set, modes, args):
        '''
        Method called when user changes mode(s) for a channel.
        '''
        # Notify plugins and log the message
        logging.debug("[MODE] %s sets %s%s %s for %s", user, "+" if set else "-", modes, args, channel)
        ext.notify(self, 'mode',
                   user=user, channel=channel, set=set, modes=modes, args=args)
        
    def topicUpdated(self, user, channel, newTopic):
        '''
        Method called when topic of channel changes or upon joining the channel.
        '''
        # Notify plugins and log message
        logging.debug("[TOPIC] <%s/%s> %s", user, channel, newTopic)
        ext.notify(self, 'topic', channel=channel, topic=newTopic, user=user)
        
    def joined(self, channel):
        '''
        Method called when bot has joined a channel.
        '''
        # Notify plugins and log the event
        logging.debug("[JOIN] %s to %s", self.nickname, channel)
        ext.notify(self, 'join', channel=channel, user=self.nickname)
        
    def userJoined(self, user, channel):
        '''
        Method called when other user has joined a channel.
        '''
        # Notify plugins and log event
        logging.debug("[JOIN] %s to %s", user, channel)
        ext.notify(self, 'join', channel=channel, user=user)
        
    def left(self, channel):
        '''
        Method called when bot has left a channel.
        '''
        # Notify plugins and log event
        logging.debug("[PART] %s from %s", self.nickname, channel)
        ext.notify(self, 'part', user=self.nickname, channel=channel)
        
    def userLeft(self, user, channel):
        '''
        Method called when other user has left a channel.
        '''
        # Notify plugins and log event
        logging.debug("[PART] %s from %s", self.nickname, channel)
        ext.notify(self, 'part', user=self.nickname, channel=channel)
        
    def kickedFrom(self, channel, kicker, message):
        '''
        Method called when bot is kicked from a channel.
        '''
        # Notify plugins and log event
        logging.debug("[KICK] %s from %s by %s (%s)", self.nickname, channel, kicker, message)
        ext.notify(self, 'kick', channel=channel, kicker=kicker, kickee=self.nickname, reason=message)
        
    def userKicked(self, kickee, channel, kicker, message):
        '''
        Method called when other user is kicked from a channel.
        '''
        # Notify plugins and log event
        logging.debug("[KICK] %s from %s by %s (%s)", kickee, channel, kicker, message)
        ext.notify(self, 'kick', channel=channel, kicker=kicker, kickee=kickee, reason=message)
        
    def nickChanged(self, nick):
        '''
        Method called when bot's nick has changed.
        '''
        # Remember new nick
        old = self.nickname
        self.nickname = nick
        
        # Notify plugins and log event
        logging.debug("[NICK] %s -> %s", old, nick)
        ext.notify(self, 'nick', old=old, new=nick)
        
    def userRenamed(self, oldname, newname):
        '''
        Method called when other user has changed their nick.
        '''
        # Notify plugins and log event
        logging.debug("[NICK] %s -> %s", oldname, newname)
        ext.notify(self, 'nick', old=oldname, new=newname)
        
    def userQuit(self, user, message):
        '''
        Method called when other user has disconnected from IRC.
        '''
        # Notify plugins and log event
        logging.debug("[QUIT] %s (%s)", user, message)
        ext.notify(self, 'quit', user=user, message=message)