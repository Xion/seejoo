'''
Created on 2010-12-10

@author: xion

Utility module.
'''
import re
import functools


###############################################################################
# Sending messages

# Limits for messages
LINE_MAX_LEN = 512
MESSAGE_MAX_LEN = 768

def say(bot, channel, messages):
    '''
    Sends message to given channel, which can also be a nick.
    '''
    # Try to get nick; if not, then just assume it's a channel message
    target = get_nick(channel) or channel
    
    # Trim and post messages
    messages = [m[:MESSAGE_MAX_LEN] for m in messages]            
    for m in messages:
        bot.msg(target, str(m), LINE_MAX_LEN)


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