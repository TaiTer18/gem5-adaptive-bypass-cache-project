#!/bin/bash
#
#SBATCH --job-name=run_ft_eval_2
#SBATCH --cpus-per-task=8
#SBATCH --time=1:00:00
#SBATCH --mem=12G

# FT split 2: 512kB and 1MB configurations.
srun python3 launch_ft_2.py 8
