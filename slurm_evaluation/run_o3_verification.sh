#!/bin/bash
#SBATCH --job-name=gem5_o3_verify
#SBATCH --cpus-per-task=8
#SBATCH --mem=16G
#SBATCH --time=1:00:00

echo "Starting targeted O3CPU verification..."
srun python3 launch_o3_verification.py 8
echo "O3CPU Verification complete!"
