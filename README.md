PyCache is an annotation language for memoization of functions in Python. Its main features are that it automatically resolves function dependencies (which, in addition to explicit arguments, may include global variables, source code, and data on disk) and automatically clears a function’s memoization cache when its code (or, transitively, that of any helper functions) changes.


## Tutorial
Consider the naive version of a recursive function that computes the Fibonacci numbers:
```python
# tests/tests.py
def fib(n):
	if n <= 1:
		return 1
	return fib(n - 1) + fib(n - 2)
```
It will run in exponential time, but we can use PyCache to automatically transform it into a memoized, linear time version. From the REPL:
```python
>>> import pycache
>>> from tests import fib
>>> fib(100)
<<< 573147844013817084101
```
This should run near-instantaneously, while the non-memoized version would never complete.

By default, pycache resolves a function's code dependencies at runtime and invalidates its cache when it detects source code changes. This can be seen by the following example:
```python
# tests/tests.py
@pycache.memoizer(memo_args = True, memo_vars = False, memo_code = True)
def foo(x):
	return bar(x)

def bar(z):
	return 2 * z

def bar2(z):
	return 3 * z
```
Again from the shell:
```python
>>> import pycache
>>> import tests
>>> tests.foo(1)
<<< 2
>>> tests.bar = tests.bar2
>>> tests.foo(1)
<<< 3
```
We see that the output of foo() correctly changes when tests.bar is rebound to the same function as tests.bar2. 

Finally, pycache calculates cache keys using the values of both function parameters and of the global and local variables accessed in a function's body.

Variable lookup and code-based cache invalidation are necessary to obtain correct behavior in the general case of functions that may access shared state and can be dynamically altered at runtime. However, they introduce substantial overhead that can in some cases negate the benefit of memoization. For this reason the user can selectively disable features by decorating functions. For instance, we could use the knowledge that fib is (1) mutation-free and (2) that it calls no functions other than itself to disable code and variable checks:
```python
@pycache.memoizer(memo_args = True, memo_vars = False, memo_code = False)
def fib2(n):
	if n <= 1:
		return 1
	return fib2(n - 1) + fib2(n - 2)
```
The user can perform this type of optimization whenever desired.

PyCache was bootstrapped in CSE401 at the University of Washington.
