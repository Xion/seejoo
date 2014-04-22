#!/usr/bin/env python
'''
Created on 05-12-2010

@author: Xion

Startup script for the bot.
'''
from optparse import OptionGroup, OptionParser # Not argparse since we target Python 2.6 as well
import os
import logging
import sys

from seejoo import bot
from seejoo.config import config


def main(argv=None):
    ''' Startup function.
    @param argv: List of command line arguments. By default, sys.argv
                (i.e. actual command line of the process) will be used.
    '''
    setup_logging()
    create_data_directory()

    config_file = get_config_file()
    try:
        config.load_from_file(config_file)
        logging.info("Config file '%s' loaded successfully.", config_file)
    except Exception, e:
        logging.fatal("Could not read specified config file '%s' (%s: %s)",
                      config_file, type(e).__name__, e)
        exit(1)

    bot.run()


def create_data_directory():
    ''' Makes sure that the data directory (where plugins can store
    some persistent information) has been created.
    @return: Path to data directory
    '''
    data_dir = os.path.expanduser("~/.seejoo/")
    try:
        os.makedirs(data_dir)
    except OSError:
        pass
    return data_dir


def setup_logging():
    ''' Initializes the log output of the bot,
    making it log to stdout in some useful fashion.
    '''
    fmt = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(fmt)
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    logger.addHandler(handler)


def get_config_file(argv=None):
    ''' Retrieves the name of the configuration file
    from command line arguments.
    '''
    parser = get_cmdline_parser()

    _, args = parser.parse_args(argv)
    if len(args) < 1:
        parser.error("You need to specify configuration file")

    return args[0]


def get_cmdline_parser(argv=None):
    ''' Creates a parser for command line arguments. '''
    return OptionParser(usage="%prog config_file")


if __name__ == '__main__':
    main()
