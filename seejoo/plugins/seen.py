'''
Plugin which offers .seen command,
to check when a person was last seen active.

Created on 2012-01-12

@author: Xion
'''
from seejoo.ext import plugin, get_storage_dir
import os
import json



@plugin
def seen_plugin(bot, event, **kwargs):
	''' Main function. Plugin is implemented as a function because
	it eliminates some redundancy in recording user's activity.
	'''
	if event == 'command' and kwargs['cmd'] == 'seen':
		return handle_seen_command(user, kwargs['args'])
	track_user_activity(event, **kwargs)

seen_plugin.commands = {'seen': "Reports last time when user was seen"}


###############################################################################
# Tracking user activity

storage_dir = get_storage_dir(seen_plugin)

def track_user_activity(user, event, **kwargs):
	''' Tracks activity of some user, recording it for further retrieving
	with .seen command.
	'''
	# ...


def format_activity_text(event, **kwargs):
	''' Creates a line of text describing an IRC event with given parameters.
	It will be recorded as user's activity and eventually displayed
	in response to .seen command.
	'''
	event_formats = {
		'join': "* %(user)s joins %(channel)s.",
		'part': "* %(user)s leaves  %(channel)s.",
		'kick': "* %(kickee)s has been kicked from %(channel)s by %(kicker)s.",
		'message': "<%(user)s> %(message)s",
		'nick': "* %(old)s changes nick to %(new)s.",
		'mode': "* %(user)s sets mode %(modes)s %(args)s",
		'topic': "* %(user)s sets topic of %(channel)s to '%(topic)s'."
	}
	

def record_activity(user, channel, text):
	''' Records activity represented by given text. '''
	activity = {}

	user_file = os.path.join(storage_dir, user)
	if os.path.exists(user_file):
		with open(user_file, 'r') as f:
			activity = json.load(f)

	activity.setdefault(channel, []).append(text)
	with open(user_file, 'w') as f:
		json.dump(f)
