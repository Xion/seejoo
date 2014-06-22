'''
Plugin which offers .seen command,
to check when a person was last seen active.

Created on 2012-01-12

@author: Xion
'''
from datetime import datetime
import json
import os
from time import time

from seejoo.ext import register_plugin, get_storage_dir, MSG_ACTION
from seejoo.util import irc


def seen_plugin(bot, event, **kwargs):
    ''' Main function. Plugin is implemented as a function because
    it eliminates some redundancy in recording user's activity.
    '''
    if event in ('init', 'tick'):
        return

    if event == 'command':  # .seen command
        user_arg = kwargs['args'].strip()
        if user_arg == irc.get_nick(kwargs['user']):
            return "You might wanna look in the mirror..."
        if user_arg == bot.nickname:
            return "Looking for me?"
        return handle_seen_command(user_arg)

    track_activity(event, **kwargs)

seen_plugin.commands = {'seen': "Reports last time when user was seen"}
register_plugin(seen_plugin)


storage_dir = get_storage_dir(seen_plugin)


# .seen command

def handle_seen_command(user):
    ''' Handle the .seen command, returning the answer: when given user
    has been last seen.
    '''
    if not user:
        return "You haven't said who you're looking for."

    user_file = os.path.join(storage_dir, user)
    if not os.path.exists(user_file):
        return "Sorry, I have never heard of '%s'." % user

    with open(user_file, 'r') as f:
        activity = json.load(f)

    channel, last_action = max(activity.iteritems(),
                               key=lambda (_, a): a['timestamp'])

    activity_time = datetime.fromtimestamp(last_action['timestamp'])
    formatted_time = activity_time.strftime("%Y-%m-%d %H:%M:%S")
    channel_part = " on %s" % channel if channel != GLOBAL_CHANNEL else ""

    return "%s was last seen%s at %s: %s" % (
        user, channel_part, formatted_time, last_action['text'])


# Tracking user activity

GLOBAL_CHANNEL = '(global)'


def track_activity(event, **kwargs):
    ''' Tracks activity of some user, recording it for further retrieving
    with .seen command.
    '''
    # retrieve user(s) for this activity
    events_to_user_refs = {
        'kick': ('kicker', 'kickee'),
        'nick': ('old', 'new'),
    }
    user_refs = events_to_user_refs.get(event, ('user',))
    users = filter(None, map(kwargs.get, user_refs))

    if users:
        # replace full user IDs with just their nicks
        for ref in user_refs:
            kwargs[ref] = irc.get_nick(kwargs[ref])

        text = format_activity_text(event, **kwargs)
        channel = kwargs.get('channel')

        for user in users:
            record_user_activity(user, channel, text)


def format_activity_text(event, **kwargs):
    ''' Creates a line of text describing an IRC event with given parameters.

    It will be recorded as user's activity and eventually displayed
    in response to .seen command.
    '''
    def format_message_event(d):
        fmt = "* %s %s" if d.get('type') == MSG_ACTION else "<%s> %s"
        return fmt % (d['user'], d['message'])

    def format_mode_event(d):
        mode_args = d['args']
        formatted_args = (" " + " ".join(mode_args)
                          if mode_args and all(mode_args)
                          else "")
        sign = "+" if d['set'] else "-"
        return "* %s sets mode %s%s%s" % (d['user'], sign,
                                          d['modes'], formatted_args),

    event_formatters = {
        'join': lambda d: "* %s joins %s." % (
            d['user'], d['channel']),
        'part': lambda d: "* %s leaves %s." % (
            d['user'], d['channel']),
        'kick': lambda d: "* %s has been kicked from %s by %s." % (
            d['kickee'], d['channel'], d['kicker']),
        'message': format_message_event,
        'nick': lambda d: "* %s changes nick to %s." % (
            d['old'], d['new']),
        'mode': format_mode_event,
        'topic': lambda d: "* %s sets topic of %s to '%s'." % (
            d['user'], d['channel'], d['topic']),
        'quit': lambda d: "* %s quits IRC (%s)." % (
            d['user'], d['message']) ,
    }

    fmt = event_formatters.get(event)
    return fmt(kwargs) if fmt else None


def record_user_activity(user, channel, text):
    ''' Records activity represented by given text. '''
    activity = {}

    user_file = os.path.join(storage_dir, irc.get_nick(user))
    if os.path.exists(user_file):
        with open(user_file, 'r') as f:
            try:
                activity = json.load(f)
            except ValueError:
                pass

    channel = channel or GLOBAL_CHANNEL
    activity[channel] = {'text': text, 'timestamp': time()}
    with open(user_file, 'w') as f:
        json.dump(activity, f)
