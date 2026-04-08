#!/bin/bash
#SBATCH --job-name=microbench_eval
#SBATCH --cpus-per-task=8
#SBATCH --mem=16G
#SBATCH --time=01:00:00

# Force dynamic native compilation safely on the remote target immediately before dispatching
cd microbench
make clean
make X86
cd ..

# Dispatch across 8 cores matching allocation
srun python3 launch_microbench_o3.py 8
