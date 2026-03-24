#!/bin/bash
#
#SBATCH --job-name=build_gem5
#SBATCH --output=slurm_evaluation/output/build.out
#SBATCH --error=slurm_evaluation/output/build.err
#SBATCH --cpus-per-task=8
#SBATCH --time=2:00:00
#SBATCH --mem=16G

scons -j 8 build/X86/gem5.opt CPU_MODELS='AtomicSimpleCPU,O3CPU,TimingSimpleCPU,MinorCPU' --gold-linker
