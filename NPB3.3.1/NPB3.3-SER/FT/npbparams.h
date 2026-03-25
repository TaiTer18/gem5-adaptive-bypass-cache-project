c CLASS = S
c  
c  
c  This file is generated automatically by the setparams utility.
c  It sets the number of processors and the class of the NPB
c  in this directory. Do not modify it by hand.
c  
        integer nx, ny, nz, maxdim, niter_default
        integer ntotal, nxp, nyp, ntotalp
        parameter (nx=64, ny=64, nz=64, maxdim=64)
        parameter (niter_default=6)
        parameter (nxp=nx+1, nyp=ny)
        parameter (ntotal=nx*nyp*nz)
        parameter (ntotalp=nxp*nyp*nz)
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
