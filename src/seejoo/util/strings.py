'''
Created on 2011-07-04

@author: xion

Utility module containing more or less general string-related functions.
'''
import re


def normalize_whitespace(string):
    '''
    Normalizes the whitespace in given string, replacing sequences of
    whitespace with single space character.
    '''
    p = re.compile(r'\s+')
    return p.sub(' ', string)


def strip_html_tags(data):
    '''
    Strips any HTML-like tags from given data.
    '''
    p = re.compile(r'<.*?>')
    return p.sub('', data)

def strip_html_entities(data):
    '''
    Strips any HTML entity references from given data.
    '''
    p = re.compile(r'&[^;]+;')
    return p.sub('', data)

def strip_html(data):
    '''
    Strips HTML tags and stuff from given text, making it plain text.
    '''
    data = strip_html_tags(data)
    data = strip_html_entities(data)
    data = normalize_whitespace(data)
    return data
