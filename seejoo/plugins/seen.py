'''
Plugin which offers .seen command,
to check when a person was last seen active.

Created on 2012-01-12

@author: Xion
'''
from seejoo.ext import register_plugin, get_storage_dir
from seejoo.util import irc
from datetime import datetime
from time import time
import os
import json


def seen_plugin(bot, event, **kwargs):
	''' Main function. Plugin is implemented as a function because
	it eliminates some redundancy in recording user's activity.
	'''
	if event in ['init', 'tick']:
		return
	if event == 'command' and str(kwargs['cmd']) == 'seen':
		return handle_seen_command(kwargs['args'])
	track_activity(event, **kwargs)

seen_plugin.commands = {'seen': "Reports last time when user was seen"}
register_plugin(seen_plugin)


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

	channel, last = max(activity.iteritems(),
						key = lambda (_, a): a['timestamp'])

	activity_time = datetime.fromtimestamp(last['timestamp'])
	formatted_time = activity_time.strftime("%Y-%m-%d %H:%M:%S")
	channel_part = " on %s" % channel if channel != GLOBAL_CHANNEL else ""

	return "%s was last seen%s at %s: %s" % (
		user, channel_part, formatted_time, last['text'])


###############################################################################
# Tracking user activity

GLOBAL_CHANNEL = '(global)'

def track_activity(event, **kwargs):
	''' Tracks activity of some user, recording it for further retrieving
	with .seen command.
	'''
	text = format_activity_text(event, **kwargs)

	# retrieve user(s) for this activity
	if event == 'kick':		users = ['kicker', 'kickee']
	elif event == 'nick':	users = ['old', 'new']
	else:
		user = kwargs.get('user')
		users = [user] if user else []

	channel = kwargs.get('channel')
	for user in users:
		record_user_activity(user, channel, text)
	

def format_activity_text(event, **kwargs):
	''' Creates a line of text describing an IRC event with given parameters.
	It will be recorded as user's activity and eventually displayed
	in response to .seen command.
	'''
	# special stuff for the most complicated 'mode' event
	mode_has_args = lambda args: args and all(args)
	format_mode_args = lambda args: " " + " ".join(args) if mode_has_args(args) else ""

	event_formatters = {
		'join': lambda d: "* %s joins %s." % (
			d['user'], d['channel']),
		'part': lambda d: "* %s leaves  %s." % (
			d['user'], d['channel']),
		'kick': lambda d: "* %s has been kicked from %s by %s." % (
			d['kickee'], d['channel'], d['kicker']),
		'message': lambda d: "<%s> %s" % (
			d['user'], d['message']),
		'nick': lambda d: "* %s changes nick to %s." % (
			d['old'], d['new']),
		'mode': lambda d: "* %s sets mode %s%s%s" % (
			d['user'], "+" if d['set'] else "-",
			d['modes'], format_mode_args(d['args'])),
		'topic': lambda d: "* %s sets topic of %s to '%s'." % (
			d['user'], d['channel'], d['topic']),
	}

	fmt = event_formatters.get(event)
	if not fmt:	return
	return fmt(kwargs)
	

def record_user_activity(user, channel, text):
	''' Records activity represented by given text. '''
	activity = {}

	user_file = os.path.join(storage_dir, irc.get_nick(user))
	if os.path.exists(user_file):
		with open(user_file, 'r') as f:
			try:				activity = json.load(f)
			except ValueError:	pass

	channel = channel or GLOBAL_CHANNEL
	activity[channel] = {'text': text, 'timestamp': time()}
	with open(user_file, 'w') as f:
		json.dump(activity, f)
