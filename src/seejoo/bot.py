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

MAX_LEN = 384


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
        
        # Join channels
        for chan in config.channels:    self.join(chan)
    
        
    def privmsg(self, user, channel, message):
        '''
        Method called upon receiving a message on a channel or private message.
        '''
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
        
        # Log message/command and notify plugins
        logging.debug ("[%s] <%s@%s> %s", "COMMAND" if is_command else "MESSAGE",
                       user, channel if not is_priv else '__priv__', message)
        ext.notify(self, 'message',
                   user=user, channel=(channel if not is_priv else None),
                   message=message, notice=False)
        
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
        
        # Serve the response
        if is_priv:
            
            # Retrieve the nick of user
            m = USER_RE.match(user)
            nick = m.groupdict().get('nick') if m else None
            
            self.msg(nick, resp, MAX_LEN)
            
        else:       self.say(channel, resp, MAX_LEN)
        logging.debug("[RESPONSE] %s", resp)