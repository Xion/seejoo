'''
Created on 08-12-2010

@author: Xion

Greetings plugin. Allows users to specify personalized greetings
and have them used by bot when they enter the channel.
'''
from seejoo.ext import Plugin, plugin


@plugin
class Greetings(Plugin):
    '''
    Greetings plugin class.
    '''
    def __init__(self):
        '''
        Constructor.
        '''
    
    def join(self, bot, channel, user):
        '''
        Called when user joins a channel.
        '''
        if user == bot.nickname:    return  # Only interested in others joining
        
        #...