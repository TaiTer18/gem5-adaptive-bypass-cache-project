#!/bin/bash
#SBATCH --job-name=gem5_synthetic
#SBATCH --cpus-per-task=8
#SBATCH --mem=16G
#SBATCH --time=1:00:00

echo "Compiling synthetic cache-killer payload on standard Linux host..."
g++ -O3 -static "synthetic_cache_killer.cpp" -o "synthetic_cache_killer.x"

echo "Deploying synthetic O3CPU verification runs..."
srun python3 "launch_synthetic_o3.py" 8
echo "Synthetic Verification complete!"
