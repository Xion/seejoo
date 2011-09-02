#!/usr/bin/env python

'''
Created on 05-12-2010

@author: Xion

Startup script for the bot.
'''
from seejoo import bot
from seejoo.config import config
import os
import logging


CONFIG_FILE = "config.yaml"
LOG_FILE = 'seejoo.log'

def main():
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
    bot.run()
    
    
if __name__ == '__main__':
    main()
