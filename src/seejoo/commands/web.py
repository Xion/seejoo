'''
Created on 2010-12-05

@author: xion

Commands used to access various web services such as Google or Wikipedia.
'''
from seejoo.ext import command


@command('test')
def ble(args):
    return "I've read %s" % args if args else "Works."