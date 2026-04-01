#!/bin/bash
#
#SBATCH --job-name=run_ft_eval
#SBATCH --cpus-per-task=8
#SBATCH --time=1:00:00
#SBATCH --mem=12G

# Start the python multi-processing script to launch simulations.
# Launching with 8 processes to match the number of cpus.
srun python3 launch_ft.py 8
