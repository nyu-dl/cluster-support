#!/bin/bash
#SBATCH --job-name=job_wgpu
#SBATCH --open-mode=append
#SBATCH --output=./%j_%x.out
#SBATCH --error=./%j_%x.err
#SBATCH --export=ALL
#SBATCH --time=00:10:00
#SBATCH --gres=gpu:1
#SBATCH --partition=p40_4,p100_4,v100_sxm2_4,dgx1
#SBATCH --mem=64G
#SBATCH -c 4

python ./test_gpu.py
