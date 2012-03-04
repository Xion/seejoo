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
import sys


def main():
    ''' Startup function. '''

    # create data directory if it doesn't exist
    data_dir = os.path.expanduser("~/.seejoo/")
    try:            os.makedirs(data_dir)
    except OSError: pass
    
    # setup logging
    fmt = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(fmt)
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    logger.addHandler(handler)
    
    # obtain config and run
    config.parse_args()
    bot.run()
    
    
if __name__ == '__main__':
    main()
