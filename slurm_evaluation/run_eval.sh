#!/bin/bash
#
#SBATCH --job-name=run_eval
#SBATCH --cpus-per-task=8
#SBATCH --time=1:00:00
#SBATCH --mem=8G

# Start the python multi-processing script to launch simulations.
srun python3 launch.py adaptive_eval 8
