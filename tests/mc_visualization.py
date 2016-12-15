import numpy as np
import matplotlib.pyplot as plt


SIZE = 20
STEPS = 1000
sigma = .2
title = 'memoized'

#@pycache.memoizer(memo_args = False, memo_vars = False, memo_code = False)
#def coefficient(distance):
#    return np.exp(-(distance/sigma)**2)

#coefficient = scipy.signal.gaussian(1, 1)
#----------------------------------------------------------------------#
#   Check periodic boundary conditions
#----------------------------------------------------------------------#

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

#----------------------------------------------------------------------#
#   Calculate internal energy
#----------------------------------------------------------------------#

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
    # return -1 * system[N,M] * (system[bc(N-1), M] \
    #                            + system[bc(N+1), M] \
    #                            + system[N, bc(M-1)] \
    #                            + system[N, bc(M+1)])

#----------------------------------------------------------------------#
#   Build the system
#----------------------------------------------------------------------#
@pycache.memoizer(memo_args = False, memo_vars = False, memo_code = False)
def build_system():
    system = np.random.random_integers(0,1,(SIZE,SIZE))
    system[system==0] =- 1

    return system

#----------------------------------------------------------------------#
#   The Main monte carlo loop
#----------------------------------------------------------------------#
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

#----------------------------------------------------------------------#
#   Run the menu for the monte carlo simulation
#----------------------------------------------------------------------#
@pycache.memoizer(memo_args = False, memo_vars = False, memo_code = False)
def run(T = 0.2, callback = None):
    print ('='*70)
    print ('\tMonte Carlo Statistics for an ising model with')
    print ('\t\tperiodic boundary conditions')
    print ('='*70)

    plt.show(block = False)
    return main(T, callback = callback)
