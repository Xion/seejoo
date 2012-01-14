'''
Plugin which offers .seen command,
to check when a person was last seen active.

Created on 2012-01-12

@author: Xion
'''
from seejoo.ext import plugin, get_storage_dir
from datetime import datetime
from time import time
import os
import json


@plugin
def seen_plugin(bot, event, **kwargs):
	''' Main function. Plugin is implemented as a function because
	it eliminates some redundancy in recording user's activity.
	'''
	if event == 'command' and kwargs['cmd'] == 'seen':
		return handle_seen_command(kwargs['args'])
	track_user_activity(event, **kwargs)

seen_plugin.commands = {'seen': "Reports last time when user was seen"}

storage_dir = get_storage_dir(seen_plugin)


###############################################################################
# .seen command

def handle_seen_command(user):
	''' Handle the .seen command, returning the answer: when given user
	has been last seen.
	'''
	user_file = os.path.join(storage_dir, user)
	if not os.path.exists(user_file):
		return "Sorry, I have never heard of '%s'." % user

	with open(user_file, 'r') as f:
		activity = json.load(f)

	most_recent = max(activity, lambda a: a['timestamp'])
	
	activity_time = datetime.fromtimestamp(a['timestamp'])
	formatted_time = activity_time.strftime("%Y-%m-%d %H:%M:%S")
	return "%s was last seen at %s: %s" % (user, formatted_time, a['text'])


###############################################################################
# Tracking user activity

def track_user_activity(event, **kwargs):
	''' Tracks activity of some user, recording it for further retrieving
	with .seen command.
	'''
	text = format_activity_text(event, **kwargs)

	channel = kwargs.get('channel')
	if event == 'kick':
		record_activity(kwargs.get('kicker'), channel, text)
		record_activity(kwargs.get('kickee'), channel, text)
	else:
		record_activity(kwargs.get('user'), channel, text)
	

def format_activity_text(event, **kwargs):
	''' Creates a line of text describing an IRC event with given parameters.
	It will be recorded as user's activity and eventually displayed
	in response to .seen command.
	'''
	event_formatters = {
		'join': lambda d: "* %s joins %s." % (d['user'], d['channel']),
		'part': lambda d: "* %s leaves  %s." % (d['user'], d['channel']),
		'kick': lambda d: "* %s has been kicked from %s by %s." % (d['kickee'], d['channel'], d['kicker']),
		'message': lambda d: "<%s> %s" % (d['user'], d['message']),
		'nick': lambda d: "* %s changes nick to %s." % (d['old'], d['new']),
		'mode': lambda d: "* %s sets mode %s%s%s"" % (
			d['user'], "+" if d['set'] else "-", " " + d['args'] if d['args'] else "",
		),
		'topic': lambda d: "* %s sets topic of %s to '%s'." % (d['user'], d['channel'], d['topic']),
	}

	fmt = event_formatters.get(event)
	if not fmt:	return
	return fmt(kwargs)
	

def record_activity(user, channel, text):
	''' Records activity represented by given text. '''
	activity = {}

	user_file = os.path.join(storage_dir, user)
	if os.path.exists(user_file):
		with open(user_file, 'r') as f:
			activity = json.load(f)

	channel = channel or '(global)'
	activity[channel] = {'event': text, 'time': time()}
	with open(user_file, 'w') as f:
		json.dump(f)
