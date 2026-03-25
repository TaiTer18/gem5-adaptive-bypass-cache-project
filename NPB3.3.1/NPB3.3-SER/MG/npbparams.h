c CLASS = S
c  
c  
c  This file is generated automatically by the setparams utility.
c  It sets the number of processors and the class of the NPB
c  in this directory. Do not modify it by hand.
c  
        integer nx_default, ny_default, nz_default
        parameter (nx_default=32, ny_default=32, nz_default=32)
        integer nit_default, lm, lt_default
        parameter (nit_default=4, lm = 5, lt_default=5)
        integer debug_default
        parameter (debug_default=0)
        integer ndim1, ndim2, ndim3
        parameter (ndim1 = 5, ndim2 = 5, ndim3 = 5)
        integer one, nv, nr, ir
        parameter (one=1)
        logical  convertdouble
        parameter (convertdouble = .false.)
        character compiletime*11
        parameter (compiletime='25 Mar 2026')
        character npbversion*5
        parameter (npbversion='3.3.1')
        character cs1*8
        parameter (cs1='gfortran')
        character cs2*8
        parameter (cs2='gfortran')
        character cs3*6
        parameter (cs3='(none)')
        character cs4*6
        parameter (cs4='(none)')
        character cs5*34
        parameter (cs5='-O3 -static -fno-second-underscore')
        character cs6*11
        parameter (cs6='-O3 -static')
        character cs7*6
        parameter (cs7='randi8')
