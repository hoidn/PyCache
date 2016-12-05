import pdb
import ast
import pycache

ms = pycache.MemoStack()
import other
def foo(x):
    ms.push(1)
    y = x + bar(x)
    return y + other.third.bazbar(x)

def bar(z):
    return 2 * z

def double(f):
    def new_f(*args, **kwargs):
        return 2 * f(*args, **kwargs)
    return new_f

def fib(n):
    if n <= 1:
        return 1
    return fib(n - 1) + fib(n - 2)

@pycache.simplememo
def fib2(n):
    if n <= 1:
        return 1
    return fib2(n - 1) + fib2(n - 2)

def test_wrap_double():
    #pdb.set_trace()
    mod = ast.parse('foo(2)')
    call = mod.body[0].value
    assert pycache.eval_node(call, context = globals()) == 12
    call2 = pycache.wrap_call(call, double)
    assert pycache.eval_node(call2, context = globals()) == 24
    # wrap_call currently copies (rather than mutates) the original node, which
    # might or might not be what we want.
    assert pycache.eval_node(call, context = globals()) == 12

#def test_wrap_memo():
#    mod = ast.

mod = ast.parse('fib(34)')

call = mod.body[0].value

#call2 = pycache.wrap_call(call, pycache.simplememo)

def dtest():
    @pycache.simplememo
    def gar():
        return 1
    return gar()

import time

print(time.time())
fib(34)
print(time.time())

#def ftest():
#    def fib(n):
#        if n <= 1:
#            return 1
#        return fib(n - 1) + fib(n - 2)
#    wrapped = pycache.simplememo(fib)
#    fib = wrapped

#fib = pycache.simplememo(fib)


#pycache.eval_node(call2, context = globals())

#expr = ast.Expression(call)

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
