'''
Created on 2010-12-10

@author: xion

Utility module containing IRC-related functions.
'''
import functools
import logging
import re


###############################################################################
# Sending messages

# Limits for messages
LINE_MAX_LEN = 512
MESSAGE_MAX_LEN = 768

def say(bot, channel, messages):
    '''
    Sends message to given channel, which can also be a nick.
    '''
    if isinstance(messages, basestring):
        messages = [messages]
    target = get_nick(channel) or channel
    
    # Trim and post messages
    messages = [msg[:MESSAGE_MAX_LEN] for msg in messages]            
    for msg in messages:
        msg = unicode(msg).encode('utf-8', 'ignore')
        bot.msg(target, msg, LINE_MAX_LEN)
        logging.debug("[SEND] <%s/%s> %s", "__me__", channel, msg)


###############################################################################
# User information extraction

# Regular expresion compiled for speed
USER_RE = re.compile(r"(?P<nick>[^\!]+)(\!(?P<id>[^\@]+)?\@(?P<host>.*))?")

def _get_host_part(part, user_host):
    '''
    Retrieves the part of user's host specified by the first parameter.
    '''
    if not user_host:   return None
    
    # Parse the host
    m = USER_RE.match(user_host)
    return m.groupdict().get(part) if m else None


# Function to retrieve specific parts
get_nick = functools.partial(_get_host_part, 'nick')
get_user_id = functools.partial(_get_host_part, 'id')
get_host = functools.partial(_get_host_part, 'host')
