#!/bin/bash
#
#SBATCH --job-name=run_bt_eval
#SBATCH --cpus-per-task=8
#SBATCH --time=1:00:00
#SBATCH --mem=16G

# Start the python multi-processing script to launch simulations.
# Launching with 8 processes.
srun python3 launch_bt.py 8
