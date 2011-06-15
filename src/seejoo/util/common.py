'''
Created on 2011-06-15

@author: xion

Contains utility functions that don't fint anywhere else.
'''
import re


def normalize_whitespace(string):
    '''
    Normalizes the whitespace in given string, replacing sequences of
    whitespace with single space character.
    '''
    p = re.compile(r'\s+')
    return p.sub(' ', string)
