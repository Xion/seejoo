'''
Created on 2010-12-05

@author: xion

Extensions module. Contains installed commands and plugins, as well as functions
to register them. Shall be used by external modules to add extensions to seejoo.
'''
import logging
import functools


###############################################################################
# Commands

_commands = {}

def register_command(name, cmd_object):
    '''
    Registers a new command. Commands are bot's utility functions that can be
    invoked on IRC by saying their names and arguments on the channel where
    bot is present (following prefix defined in configuration) or by sending
    a private message to the bot (with or without prefix).
    @param name: A name of the command. This is also the phrase used to invoke it
    @param cmd_object: A callable object which performs the command's action.
                       It should accept a single argument which will be
                       a string containing command's invocation parameters.
    '''
    if not name or len(name) == 0:
        logging.error('Command name must not be empty.') ; return
    if name in _commands:
        logging.error('Duplicate command name "%s"', name) ; return
    if not callable(cmd_object):
        logging.error('Command object "%s" is not callable.', str(cmd_object)) ; return
        
    _commands[name] = cmd_object
    
    
def command(name):
    '''
    Decorator functions for registering commands easily.
    '''
    return functools.partial(register_command, name)


def get_command(cmd):
    '''
    Retrieves a command object associated with given name.
    '''
    global _commands
    return _commands.get(cmd)


###############################################################################
# Plugins

# NYI