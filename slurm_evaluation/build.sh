#!/bin/bash
#
#SBATCH --job-name=build_gem5
#SBATCH --cpus-per-task=8
#SBATCH --time=1:00:00
#SBATCH --mem=16G


cd "$SLURM_SUBMIT_DIR"
if [ ! -f "SConstruct" ] && [ -f "../SConstruct" ]; then
    cd ..
fi

scons -j 8 build/X86/gem5.opt CPU_MODELS='AtomicSimpleCPU,O3CPU,TimingSimpleCPU,MinorCPU' --gold-linker
