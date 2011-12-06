'''
Created on 2010-12-05

@author: xion

Standard useful commands, such as evaluation of expressions.
'''
from multiprocessing import Process, Pipe
from seejoo.ext import command
import math
import os



###############################################################################
# Evaluation of mathematical expressions

# Sandbox process and pipe to communicate with it
eval_pipe_parent = None ; eval_pipe_child = None
eval_process = None

# Forbidden functionality
FORBIDDEN_GLOBALS = ['__package__', '__file__', '__name__', '__doc__']
FORBIDDEN_BUILTINS = ['__import__', 'eval', 'execfile', 'compile', 'dir', 'open', 'exit', 'quit']

# Worker function for the evaluations; runs in different process
def _eval_worker(pipe):
    '''
    Pops the incoming expressions from given Pipe, evaluates
    them and sends the back. Continues indefinitely.
    '''
    # Construct a (relatively) safe dictionary of globals
    # to be used by evaluated expressions
    g = math.__dict__.copy()
    g['__builtins__'] = __builtins__.copy()
    for func in FORBIDDEN_BUILTINS:
        if func in g['__builtins__']:
            del g['__builtins__'][func]
    for func in FORBIDDEN_GLOBALS:
        if func in g:   del g[func]
        
    while True:
        try:                exp = pipe.recv()
        except EOFError:    return
        
        # Evaluate expression
        try:
            res = eval(exp, g)
            res = "= " + str(res)
        except SyntaxError:         res = "Syntax error."
        except ValueError:          res = "Evaluation error."
        except TypeError:           res = "Type mismatch."
        except OverflowError:       res = "Overflow."
        except FloatingPointError:  res = "Floating point exception."
        except ZeroDivisionError:   res = "Division by zero."
        except KeyError:            res = "Key not found."
        except NameError:           res = "Unknown or forbidden function."
        except MemoryError:         res = "Out of memory."
        except KeyboardInterrupt:   exit(1)  # Timeout
        except Exception:           res = "Error."

        # Check whether the result isn't obscenely big
        try:
            if res and len(res) > 1024:
                res = "Too long result."
        except TypeError, AttributeError: pass
        
        # Push the result via pipe
        pipe.send(res)
        

# Timeout for evaluation in seconds
EVAL_TIMEOUT = 5

@command('c') 
def evaluate_expression(exp):
    '''
    Evaluates given expression.
    '''    
    if not exp:         return "No expression supplied."
    exp = str(exp)
    
    # Setup evaluation process if it's not present
    global eval_process, eval_pipe_parent, eval_pipe_child
    if not eval_process:
        eval_pipe_parent, eval_pipe_child = Pipe()
        eval_process = Process(name = "seejoo_eval", target = _eval_worker, args = (eval_pipe_child,))
        eval_process.daemon = True
        eval_process.start()
    
    # Push expression through the pipe and wait for result
    eval_pipe_parent.send(exp)
    if eval_pipe_parent.poll(EVAL_TIMEOUT):
        res = str(eval_pipe_parent.recv())
        res = filter(lambda x: ord(x) >= 32, res)   # Sanitize result
        return res        
    else:
        # Evaluation timed out; kill the process and return error
        os.kill(eval_process.pid, 9)
        os.waitpid(eval_process.pid, os.WUNTRACED)
        eval_process = None
        return "Operation timed out."
