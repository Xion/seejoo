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
        
        
    def message(self, bot, channel, user, type):
        '''
        Called when bot "hears" a message.
        '''
        if not channel: return          # Only interested in channel messages
        nick = util.get_nick(user)
        
        # Collect messages pertaining to this user
        messages = [] ; files = []
        for recp in self._list_recipients():
            glob = urllib.unquote(recp)
            if fnmatch.fnmatch(nick, glob):
                
                # Read messages from file
                file = self._get_filename(glob)
                with open(file) as f:
                    messages.append(json.load(f))
                files.append(file)
                    
        # Format and send them
        msgs = []
        for message in messages:
            msg_time = datetime.fromtimestamp(message['timestamp'])
            msg = "%s <%s> %s" % (str(msg_time), message['from'], message['message'])
            msgs.append(msg)
        util.say(bot, channel, msgs)
        
        # Delete files
        for file in files:  os.unlink(file)
        
        # Log delivery
        log_file = os.path.join(self.dir, "delivery.log")
        with open(log_file, 'a') as log:
            log.writelines("%s <- %s" % (nick, m) for m in msgs)
            
        
    def command(self, bot, user, cmd, args):
        '''
        Called when user issues a command.
        '''
        nick = util.get_nick(user)
        if cmd != 'msg':    return
        
        # Get recipient and message from arguments
        try:
            recipient, message = re.split(r"\s+", args, 2)
        except ValueError:  message = None
        if not message: return "Message shall not be empty."
        
        # Store it
        self._store_message(nick, recipient, message)
        return "I will notify %s should they appear." % recipient