#!/bin/bash
#SBATCH --job-name=synthetic_eval
#SBATCH --cpus-per-task=8
#SBATCH --mem=16G
#SBATCH --time=01:00:00

srun python3 launch_synthetic_o3.py 8
