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
            g = math.__dict__.copy()
            g['__builtins__'] = __builtins__.copy()
	    for func in ['__import__', 'eval', 'exec', 'dir', 'open']:
	        del g['__builtins__'][func]
            
            # Evaluate expression
            try:                res = eval(exp, g)
            except SyntaxError: return "Syntax error."
            except ValueError:  return "Evaluation error."
	    except NameError:	return "Unknown or forbidden function."
            except MemoryError: return "Out of memory."
	    except Exception:	return "Error."
        
    return "= " + str(res)
