'''
Created on 12-12-2010

@author: Xion

Memo plugin module.
'''
import re
import json
import urllib
import fnmatch
import os
import time
from datetime import datetime
from seejoo.ext import Plugin, plugin, get_storage_dir
from seejoo import util


@plugin
class Memos(Plugin):
    '''
    Memo plugin. Allows users to leave messages to be delivered to others.
    '''
    def __init__(self):
        '''
        Constructor
        '''
        self.dir = get_storage_dir(self)
        
    def _list_recipients(self):
        '''
        Lists recipients of the messages stored by the bot.
        This is a generator function.
        '''
        for file in fnmatch.filter(os.listdir(self.dir), "*.json"):
            name, _ = os.path.splitext(file)
            yield urllib.unquote(name)
            
    def _get_filename(self, recipient):
        '''
        Get file name for storing messages to given recipient.
        '''
        return os.path.join(self.dir, urllib.quote(recipient, '') + ".json")
            
    def _store_message(self, sender, recipient, message):
        '''
        Stores a message for to given recipient, sent by given sender.
        '''
        item = { 'from': sender, 'message': message, 'timestamp': time.time() }
        
        # Read the current messages to this recipient
        file = self._get_filename(recipient)
        if os.path.exists(file):
            with open(file) as f:   items = json.load(f)
        else:   items = []
        
        # Add this one and save
        items.append(item)
        with open(file, 'w') as f:  json.dump(items, f)
        
        
    def message(self, bot, channel, user, message, type):
        '''
        Called when bot "hears" a message.
        '''
        if not channel: return          # Only interested in channel messages
        nick = util.get_nick(user)
        
        # Collect messages pertaining to this user
        messages = [] ; files = []
        for recp in self._list_recipients():
            if fnmatch.fnmatch(nick, recp):
                
                # Read messages from file
                file = self._get_filename(recp)
                with open(file) as f:
                    messages.extend(json.load(f))
                files.append(file)
                    
        # Format and send them
        msgs = []
        for message in messages:
            msg_time = datetime.fromtimestamp(message['timestamp'])
            msg_time = msg_time.strftime("%Y-%m-%d %H:%M:%S")
            
            msg = "%s <%s> %s: %s" % (msg_time, message['from'], nick, message['message'])
            msgs.append(msg)
        util.say(bot, channel, msgs)
        
        # Delete files
        for file in files:  os.unlink(file)
        
        # Log delivery
        log_file = os.path.join(self.dir, "delivery.log")
        with open(log_file, 'a') as log:
            log.writelines(m + "\n" for m in msgs)
            
        
    def command(self, bot, user, cmd, args):
        '''
        Called when user issues a command.
        '''
        if cmd != 'msg':    return
        nick = util.get_nick(user)
        
        # Forbid sending messages to the bot itself
        if nick == bot.nickname:    return "I'm here, y'know." 
        
        # Get recipient and message from arguments
        try:
            recipient, message = re.split(r"\s+", args, 1)
        except ValueError:  message = None
        if not message: return "Message shall not be empty."
        
        # Store it
        self._store_message(nick, recipient, message)
        return "I will notify %s should they appear." % recipient