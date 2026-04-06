#!/bin/bash
#SBATCH --job-name=synthetic_eval
#SBATCH --cpus-per-task=1
#SBATCH --time=01:00:00

python3 launch_synthetic_o3.py
