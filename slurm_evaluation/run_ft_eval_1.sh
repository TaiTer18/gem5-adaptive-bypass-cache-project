#!/bin/bash
#
#SBATCH --job-name=run_ft_eval_1
#SBATCH --cpus-per-task=8
#SBATCH --time=1:00:00
#SBATCH --mem=12G

# FT split 1: 128kB and 256kB configurations.
srun python3 launch_ft_1.py 8
