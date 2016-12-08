import pdb
import ast
from pycache import pycache
import time
from fib import fib

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

#def fib(n):
#    if n <= 1:
#        return 1
#    return fib(n - 1) + fib(n - 2)

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

#def test_wrap_memoize():
#    """
#    Test basic memoization of function calls.
#    """
#    wm = pycache.WrapModule('pycache.simplememo')
#    code = """
#def fib(n):
#    if n <= 1:
#        return 1
#    return fib(n - 1) + fib(n - 2)
#print(fib(34))
#    """
#    tree = ast.parse(code)
#    wm.visit(tree)
#    start = time.time()
#    pycache.exec_node(tree)
#    #pycache.exec_node(tree, glob = globals(), context = globals())
#    elapsed = time.time() - start
#    # Should have run the fast, memoized version
#    assert elapsed < 0.1

def test_simplememo():
    start = time.time()
    fib(35)
    elapsed = time.time() - start
    # Should have run the fast, memoized version
    assert elapsed < 0.1
    
