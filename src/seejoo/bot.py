'''
Created on 05-12-2010

@author: Xion

Module containing the Bot class, derived from IRCClient.
'''
from seejoo.config import config
from twisted.words.protocols.irc import IRCClient


class Bot(IRCClient):
    
    def __init__(self, *args, **kwargs):
        self.nickname = config.nickname
    
    def signedOn(self):
        '''
        Method called upon successful connection to IRC server.
        '''
        self.factory.resetDelay()
        
        # Join channels
        for chan in config.channels:    self.join(chan)