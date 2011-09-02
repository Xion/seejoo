'''
Created on 08-12-2010

@author: Xion

Greetings plugin. Allows users to specify personalized greetings
and have them used by bot when they enter the channel.
'''
import json
import os.path
from seejoo.ext import Plugin, plugin, get_storage_dir
from seejoo.util import irc


@plugin
class Greetings(Plugin):
    '''
    Greetings plugin class.
    '''
    commands = { 'greet': 'Sets a greeting that bot will say when you enter the channel' }
    
    def __init__(self):
        '''
        Constructor.
        '''
        self.greets = {}
        
        # Load the greets
        self.file = get_storage_dir(self) + 'greets.json'
        self._load()
        
    def _load(self):
        '''
        Loads the greetings from internal file.
        '''
        if os.path.exists(self.file):
            with open(self.file) as f:
                self.greets = json.load(f) 
        
    def _save(self):
        '''
        Saves the greetings to internal file.
        '''
        with open(self.file, 'w') as f:
            json.dump(self.greets, f)
    
    def join(self, bot, channel, user):
        '''
        Called when user joins a channel.
        '''
        # Retrieve the nick
        nick = irc.get_nick(user)
        if nick == bot.nickname:    return  # Only interested in others joining
        
        # Check if we have greeting and serve it
        greet = self.greets.get(nick)
        if greet:   irc.say(bot, channel, greet)
            
    def command(self, bot, user, cmd, args):
        '''
        Called when user issues a command.
        '''
        if cmd != 'greet': return  # Only interested in this command
        
        # Remember the greeting
        nick = irc.get_nick(user)
        self.greets[nick] = str(args) if args else None
        self._save()
        
        # Serve a response
        return "Greeting %s for user '%s'" % ('set' if args else 'reset', nick)
