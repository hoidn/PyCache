Pre-proposal:
https://docs.google.com/a/uw.edu/document/d/1azKSmGN7TZEMs598tSU1CD8NxhmtoxmuFiUmjzoYx4M/edit?usp=sharing

5.2:
https://docs.google.com/a/uw.edu/document/d/1IHGD7ZW8ZqL8i8GRL6Ro5SXFCS2x8GRr773njwle7Qs/edit?usp=sharing

5.3:
https://docs.google.com/a/uw.edu/document/d/1CnAfqsJpNaZ3ftw2EbG9nV_ofRsp9LGy3VaunJZntXU/edit?usp=sharing

5.4:
https://docs.google.com/a/uw.edu/document/d/1VirNg7QupR3X8ZTWfYDRsLCjBV7cgi9_Uh0mDs2Ntsc/edit?usp=sharing

## Tutorial
Consider the naive version of a recursive function that computes the Fibonacci numbers:
```python
# tests/tests.py
def fib(n):
	if n <= 1:
		return 1
	return fib(n - 1) + fib(n - 2)
```
It will run in exponential time, but we can use pycache to automatically transform it into a memoized, linear time version. From the REPL, or in a module:
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

Finally, pycache calculates cache keys using the values of both function parameters and of the global and local variables accessed in a function's body. TODO add an example demonstrating this once we've merged in that functionality.

Variable lookup and code-based cache invalidation are necessary to obtain correct behavior in the general case of functions that may access shared state and can be dynamically altered at runtime. However, they introduce substantial overhead that can in some cases negate the benefit of memoization. For this reason the user can selectively disable features by decorating functions. For instance, we could use the knowledge that fib is (1) mutation-free and (2) that it calls no functions other than itself to disable code and variable checks:
```python
@pycache.memoizer(memo_args = True, memo_vars = False, memo_code = False)
def fib2(n):
	if n <= 1:
		return 1
	return fib2(n - 1) + fib2(n - 2)
```
The user can perform this type of optimization whenever desired.

In the longer example below, we use PyCache in an application of the Metropolis-Hastings algorthim to the 2D Ising model (based on an example found online):


```python
import numpy as np
import matplotlib.pyplot as plt


SIZE = 20
STEPS = 1000
sigma = .2
title = 'memoized'

#   Check periodic boundary conditions

@pycache.memoizer(memo_args = False, memo_vars = False, memo_code = False)
def update(arr, nstep):
    if nstep % 10 == 0:
        ax.set_title("%s: step %d" % (title, nstep))
        ax.imshow(arr, interpolation = 'none')
        fig.canvas.draw()
    
fig, ax = plt.subplots()

@pycache.memoizer(memo_args = False, memo_vars = False, memo_code = False)
def bc(i):
    if i+1 > SIZE-1:
        return 0
    if i-1 < 0:
        return SIZE-1
    else:
        return i

#   Calculate internal energy
@pycache.memoizer(memo_args = False, memo_vars = False, memo_code = False)
def ratio(i, j, k, l):
    return np.exp(-(np.sqrt((k - i)**2 + 1 * (l - j)**2)/sigma)**2)
    #return coefficient(np.sqrt((k - i)**2 + (l - j)**2))
    #return  6 - (i + j - N - M)


@pycache.memoizer(memo_args = False, memo_vars = False, memo_code = False, custom_cache = "[system[N - 2 : N + 3, M - 2 : M + 3]]")
def energy(system = [], N = 0, M = 0):
    ret = -1 * system[N,M]
    tmp = 0
    for i in range(max(0, N - 2), min(N + 3, SIZE)):
        for j in range(max(0, M - 2), min(M + 3, SIZE)):
            if i == N and j == M:
                continue
            for k in range(max(0, N - 2), min(N + 3, SIZE)):
                for l in range(max(0, M - 2), min(M + 3, SIZE)):
                    if i == k and j == l:
                        continue
                    if k == N and l == M:
                        continue
                    tmp += ratio(i, j, k, l) * system[i][j] * system[k][l]
    return ret * tmp

#   Build the system
@pycache.memoizer(memo_args = False, memo_vars = False, memo_code = False)
def build_system():
    system = np.random.random_integers(0,1,(SIZE,SIZE))
    system[system==0] =- 1

    return system

#   The Main monte carlo loop
@pycache.memoizer(memo_args = False, memo_vars = False, memo_code = False)
def main(T, callback = None):
    system = build_system()
    total = 0.

    for step, x in enumerate(range(STEPS)):
        M = np.random.randint(0,SIZE)
        N = np.random.randint(0,SIZE)

        E0 = energy(system = system, N = N, M = M)
        system[N,M] *= -1
        E1 = energy(system = system, N = N, M = M)
        system[N,M] *= -1
        E =  (E1 - E0)
        #E = -2. * energy(system = system, N = N, M = M)

        #print(E)
        if E <= 0.:
            system[N,M] *= -1
        elif np.exp(-1./T*E) > np.random.rand():
            system[N,M] *= -1
        update(system, step)
    return system

@pycache.memoizer(memo_args = False, memo_vars = False, memo_code = False)
def run(T = 0.2, callback = None):
    plt.show(block = False)
    return main(T, callback = callback)
```
