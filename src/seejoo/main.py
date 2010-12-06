'''
Created on 05-12-2010

@author: Xion

Main module, containing the startup code for IRC bot.
'''
from seejoo import bot
from seejoo.config import config
from twisted.internet import reactor
from twisted.internet.protocol import ReconnectingClientFactory
import os


class BotFactory(ReconnectingClientFactory): 
    protocol = bot.Bot


###############################################################################
# Starting point

CONFIG_FILE = "config.yaml"
def start():
    '''
    Startup function.
    '''
    # Read the config from default config file if it exists
    # and PyYAML package is present
    try:
        import yaml                                                 # @UnusedImport
        if os.path.exists(CONFIG_FILE): config.load_from_file(CONFIG_FILE)
    except ImportError:
        pass
    
    # Read the configuration from command line
    config.parse_args()
    
    # Start the bot
    reactor.connectTCP(config.server, config.port, BotFactory())    # @UndefinedVariable
    reactor.run()                                                   # @UndefinedVariable
    
    
if __name__ == '__main__':
    start()