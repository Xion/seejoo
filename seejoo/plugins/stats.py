'''
Created on 08-12-2010

@author: Xion

Statistics plugin.
'''
from seejoo.ext import Plugin, plugin


@plugin
class Statistics(Plugin):
    '''
    Stats plugin. Gathers statistics about users' IRC activities and
    displays them when requested.
    '''
    def __init__(self):
        '''
        Constructor.
        '''
        pass