'''
Created on 05-12-2010

@author: Xion

Main module, containing the necessary IRC classes.
'''
from twisted.words.protocols.irc import IRCClient
from twisted.internet.protocol import ReconnectingClientFactor
from twisted.internet import reactor


class Bot(IRCClient):

    nickname = 'seejoo'

    def signedOn(self):
        self.factory.resetDelay()
        self.join('#cipra')


class BotFactory(ReconnectingClientFactor):
    protocol = Bot


if __name__ == '__main__':
    reactor.connectTCP('irc.freenode.net', 6667, BotFactory())
    reactor.run()
