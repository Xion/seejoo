"""
Created on 12-12-2010

@author: Xion

Memo plugin module.
"""
from __future__ import unicode_literals

from datetime import datetime
import fnmatch
import json
import os
import time
import urllib

from seejoo.ext import Plugin, plugin, get_storage_dir
from seejoo.util import irc


@plugin
class Memos(Plugin):
    """Memo plugin.
    Allows users to leave messages to be delivered to others.
    """
    commands = {
        'msg': ("Leave a message for particular user, "
                "e.g.: #cmd# some_one You owe me $10!"),
    }

    def __init__(self):
        self.dir = get_storage_dir(self)

    def _list_recipients(self):
        """Lists recipients of the messages stored by the bot.
        :return: A generator function yielding recipients
        """
        for filename in fnmatch.filter(os.listdir(self.dir), "*.json"):
            name, _ = os.path.splitext(filename)
            yield urllib.unquote(name)

    def _get_filename(self, recipient):
        """Get file name for storing messages to given recipient."""
        filename = urllib.quote(recipient, '')
        return os.path.join(self.dir, filename + ".json")

    def _store_message(self, sender, recipient, message):
        """Stores a message for to given recipient, sent by given sender."""
        item = {
            'from': sender,
            'message': message,
            'timestamp': time.time()
        }

        # Read the current messages to this recipient
        filename = self._get_filename(recipient)
        if os.path.exists(filename):
            with open(filename) as f:
                items = json.load(f)
        else:
            items = []

        # Add this one and save
        items.append(item)
        with open(filename, 'w') as f:
            json.dump(items, f)

    def message(self, bot, channel, user, message, type):
        """Called when bot "hears" a message."""
        if not channel:
            return          # Only interested in channel messages
        nick = irc.get_nick(user)

        # Collect messages pertaining to this user
        messages = []
        files = []
        for recp in self._list_recipients():
            if fnmatch.fnmatch(nick, recp):
                file = self._get_filename(recp)
                with open(file) as f:
                    messages.extend(json.load(f))
                files.append(file)

        # Format and send them
        msgs = []
        for message in messages:
            msg_time = datetime.fromtimestamp(message['timestamp'])
            msg_time = msg_time.strftime("%Y-%m-%d %H:%M:%S")

            msg = "%s <%s> %s: %s" % (
                msg_time, message['from'], nick, message['message'])
            msgs.append(msg)
        irc.say(bot, channel, msgs)

        # Delete files
        for file in files:
            os.unlink(file)

        # Log delivery
        log_file = os.path.join(self.dir, "delivery.log")
        with open(log_file, 'a') as log:
            log.writelines((m + os.linesep).encode('utf-8', 'ignore')
                           for m in msgs)

    def command(self, bot, channel, user, cmd, args):
        """Called when user issues a command."""
        if cmd != 'msg':
            return
        nick = irc.get_nick(user)

        # Forbid sending messages to the bot itself
        if nick == bot.nickname:
            return "I'm here, y'know."

        # Get recipient and message from arguments
        try:
            recipient, message = args.split(None, 1)
        except ValueError:
            message = None
        if not message:
            return "Message shall not be empty."

        # Store it
        self._store_message(nick, recipient, message)
        return "I will notify %s should they appear." % recipient
