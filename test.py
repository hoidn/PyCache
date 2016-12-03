import ast
import inspect
import astor
from meta.decompiler import decompile_func


def foo(x):
    y = x + bar(x)
    return y  

def bar(z):
    return 2 * z

def double(f):
    def new_f(*args, **kwargs):
        return 2 * f(*args, **kwargs)
    return new_f

def wrap_call(call_node, wrapper):
    subtree =\
        ast.Call(
            func = ast.Name(id = wrapper.__name__, ctx = ast.Load()),
            args = [ast.Name(id = 'foo', ctx = ast.Load())],
            keywords = []
        )
    call_node.func = ast.fix_missing_locations(subtree)
    return call_node

def eval_call(call_node):
    expr = ast.Expression(call_node)
    code = compile(expr, '', 'eval')
    context = {}
    return eval(code, globals(), context)

#mod = ast.parse('foo(2)')
#
#call = mod.body[0].value
#
#expr = ast.Expression(call)
#
#code = compile(expr, '', 'eval')
#
#context = {}
#
#eval(code, globals(), context)
#
#src = '[i**2 for i in range(10)]'
#
#b = ast.parse(src, mode='eval')
#
#eval(compile(b, '', 'eval'))
#
