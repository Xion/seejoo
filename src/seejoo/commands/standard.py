'''
Created on 2010-12-05

@author: xion

Standard useful commands, such as evaluation of expressions.
'''
from seejoo.ext import command
import math
from multiprocessing import Process, Pipe


@command('test')
def ble(arg, **kwargs):
    return "I've read %s" % arg if arg else "Works."

@command('hi')
def hello(arg, **kwargs):
    return "Hello."


###############################################################################
# Evaluation of mathematical expressions

# Sandbox process and pipe to communicate with it
eval_pipe_parent = None ; eval_pipe_child = None
eval_process = None

# Worker function for the evaluations; runs in different process
def _eval_worker(pipe):
    '''
    Pops the incoming expressions from given Pipe, evaluates
    them and sends the back. Continues indefinetaly.
    '''
    # Construct a (relatively) safe dictionary of globals
    # to be used by evaluated expressions
    g = math.__dict__.copy()
    g['__builtins__'] = __builtins__.copy()
    for func in ['__import__', 'eval', 'dir', 'open', 'exit']:
        del g['__builtins__'][func]
        
    while True:
        try:                exp = pipe.recv()
        except EOFError:    return
        
        # Evaluate expression
        try:
            res = eval(exp, g)
            res = "= " + str(res)
        except SyntaxError: res = "Syntax error."
        except ValueError:  res = "Evaluation error."
        except NameError:   res = "Unknown or forbidden function."
        except MemoryError: res = "Out of memory."
        except Exception:   res = "Error."

        # Check whether the result isn't obscenely big
        try:
            if res and len(res) > 1000:
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
        eval_process = Process(name="seejoo_eval", target=_eval_worker, args=(eval_pipe_child,))
        eval_process.daemon = True
        eval_process.start()
    
    # Push expression through the pipe and wait for result
    eval_pipe_parent.send(exp)
    if eval_pipe_parent.poll(EVAL_TIMEOUT):
        return str(eval_pipe_parent.recv())
    else:
        # Evaluation timed out; kill the process and return error
        eval_process.terminate()
        eval_process = None
        return "Operation timed out."
