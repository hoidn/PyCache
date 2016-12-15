import numpy as np
SIZE = 100
STEPS = 10
#----------------------------------------------------------------------#
#   Check periodic boundary conditions
#----------------------------------------------------------------------#
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

#@pycache.memoizer()
def ratio(i, j, N, M):
    return  6 - (i + j - N - M)


@pycache.memoizer(memo_args = False, memo_vars = False, memo_code = False, custom_cache = "[system[N - 3 : N + 4, M - 3 : M + 4]]")
def energy(system = [], N = 0, M = 0):
    ret = -1 * system[N,M]
    tmp = 0
    for i in range(max(0, N - 3), min(N + 4, SIZE)):
        for j in range(max(0, M - 3), min(M + 4, SIZE)):
            if i == N and j == M:
                continue
            for k in range(max(0, N - 3), min(N + 4, SIZE)):
                for l in range(max(0, M - 3), min(M + 4, SIZE)):
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
def build_system():
    system = np.random.random_integers(0,1,(SIZE,SIZE))
    system[system==0] =- 1

    return system

#----------------------------------------------------------------------#
#   The Main monte carlo loop
#----------------------------------------------------------------------#
def main(T):
    system = build_system()

    for step, x in enumerate(range(STEPS)):
        M = np.random.randint(0,SIZE)
        N = np.random.randint(0,SIZE)

        E = -2. * energy(system = system, N = N, M = M)

        if E <= 0.:
            system[N,M] *= -1
        elif np.exp(-1./T*E) > np.random.rand():
            system[N,M] *= -1
    print(system)

#----------------------------------------------------------------------#
#   Run the menu for the monte carlo simulation
#----------------------------------------------------------------------#
def run():
    print ('='*70)
    print ('\tMonte Carlo Statistics for an ising model with')
    print ('\t\tperiodic boundary conditions')
    print ('='*70)

    print ("Choose the temperature for your run (0.1-100)")
    T = float(input())
    main(T)
