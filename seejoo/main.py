#!/usr/bin/env python

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
import logging


class BotFactory(ReconnectingClientFactory): 
    protocol = bot.Bot


###############################################################################
# Starting point

CONFIG_FILE = "config.yaml"
LOG_FILE = 'seejoo.log'

def start():
    '''
    Startup function.
    '''
    # Create data directory if it doesn't exist
    data_dir = os.path.expanduser("~/.seejoo/")
    try:            os.makedirs(data_dir)
    except OSError: pass
    
    # Set up logging
    fmt = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    handler = logging.FileHandler(data_dir + LOG_FILE)
    handler.setFormatter(fmt)
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    logger.addHandler(handler)
    
    # Read the config from default config file if it exists
    # and PyYAML package is present
    try:
        import yaml                                                 # @UnusedImport
        if os.path.exists(CONFIG_FILE): config.load_from_file(CONFIG_FILE)
    except ImportError:
        logging.warning("No yaml library found -- will not parse configuration files")
    
    # Read the configuration from command line
    config.parse_args()
    
    # Start the bot
    reactor.connectTCP(config.server, config.port, BotFactory())    # @UndefinedVariable
    reactor.run()                                                   # @UndefinedVariable
    
    
if __name__ == '__main__':
    start()
