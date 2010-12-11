'''
Created on 2010-12-05

@author: xion

Standard useful commands, such as evaluation of expressions.
'''
from seejoo.ext import command
import math


@command('test')
def ble(arg, **kwargs):
    return "I've read %s" % arg if arg else "Works."

@command('hi')
def hello(arg, **kwargs):
    return "Hello."


###############################################################################
# Math

@command('c') 
def evaluate_expression(exp):
    '''
    Evaluates given expression.
    '''
    if not exp: res = None
    else:
        exp = str(exp)
        if len(exp) == 0:   res = None
        else:
            
            # Construct a (relatively) safe dictionary of globals
            # to be used by evaluated expressions
            def _imp(name, globals={}, locals={}, from_list=[], level=-1):
                raise ImportError
            g = math.__dict__.copy()
            g['__builtins__'] = __builtins__.copy()
            g['__builtins__']['__import__'] = _imp
            
            # Evaluate expression
            try:                res = eval(exp, g)
            except SyntaxError: return "Syntax error."
            except ValueError:  return "Evaluation error."
            except ImportError: return "Sorry, only math allowed."
            except MemoryError: return "Out of memory."
        
    return "= " + str(res)