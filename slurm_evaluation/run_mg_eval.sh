#!/bin/bash
#
#SBATCH --job-name=run_mg_eval
#SBATCH --cpus-per-task=8
#SBATCH --time=1:00:00
#SBATCH --mem=16G

# Start the python multi-processing script to launch simulations.
# Launching with 8 processes to match the number of cpus.
srun python3 launch_mg.py 8
