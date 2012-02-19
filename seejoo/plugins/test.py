'''
Test plugin.
@author Karol Kuczmarski
'''
from seejoo.ext import plugin, Plugin
import logging


@plugin
class Test(Plugin):
	''' Test plugin. It does almost nothing, but it verbose at doing so,
	and can be used to test functionality related to plugins.
	'''
	def __call__(self, bot, event, **kwargs):
		logging.info("Test plugin received event: %s(%s)", event,
					 ", ".join("%s=%s" % arg for arg in kwargs.iteritems()))
