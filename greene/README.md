# Greene tutorial

This tutorial aims to help with your migration from the Prince cluster (retires early 2021). It assumes some knowledge of Slurm, ssh and terminal. It assumes that one can connect to Greene ([same way](https://github.com/nyu-dl/cluster-support/tree/master/client) as to Prince).

Official Greene docs & overview: 
https://sites.google.com/a/nyu.edu/nyu-hpc/documentation/greene
https://sites.google.com/a/nyu.edu/nyu-hpc/systems/greene-cluster

**Content:**
1. Greene login nodes
2. Cluster overview
3. Singularity - running jobs within a container
4. Running a batch job with singularity
5. Setting up a simple sweep over a hyper-parameter using Slurm array job.
6. Port forwarding to Jupyter Lab
7. Using a python-based [Submitit](https://github.com/facebookincubator/submitit) framework on Greene

## Greene login nodes

* greene.hpc.nyu.edu (balancer)
* log-1.hpc.nyu.edu
* log-2.hpc.nyu.edu

You have to use NYU HPC account to login, username is the same as your NetID.

Login nodes are accessible from within NYU network, i.e. one can connect from CIMS `access1` node, check [ssh config](https://github.com/nyu-dl/cluster-support/blob/master/client/config) for details.

Login node should not be used to run anything related to your computations, use it for file management (`git`, `rsync`), jobs management (`srun`, `salloc`, `sbatch`).

## Cluster overview

|Number of nodes|CPU cores|GPU|RAM|
|---------------|---------|---|---|
|524|48|-|180G|
|40|48|-|369G|
|4|96|-|3014G **(3T)**|
|10|48|4 x V100 32G (PCIe)|369G|
|65|48|4 x **RTX8000 48G**|384G|

**quotas**:

|filesystem|env var|what for|flushed|quota|
|----------|-------|--------|-------|-----|
|/archive|$ARCHIVE|long term storage|NO|2TB/20K inodes|
|/home|$HOME|probably nothing|NO|50GB/30K inodes|
|/scratch|$SCRATCH|experiments/stuff|YES (60 days)|5TB/1M inodes|

```
echo $SCRATCH
/scratch/ik1147
```

### Differences with Prince

* Strong preference **for Singularity** / not modules.
* GPU specification through `--gres=gpu:{rtx8000|v100}:1` (Prince uses/used partitions)
* Low inode quota on home fs (~30k files)
* No beegfs

## Singularity

One can read white paper here: https://arxiv.org/pdf/1709.10140.pdf

The main idea of using a container is to provide an isolated user space on a compute node and to simplify the node management (security and updates).

### Getting a container image

Each singularity container has a definition file (`.def`) and the image file (`.sif`). Lets consider the following container:

`/scratch/work/public/singularity/cuda10.1-cudnn7-devel-ubuntu18.04-20201207.def`
`/scratch/work/public/singularity/cuda10.1-cudnn7-devel-ubuntu18.04-20201207.sif`

Definiton file contains all commands which are executed along the way when the image OS is created, take a look!

This particular image will have CUDA 10.1 with cudnn 7 libs within Ubuntu 18.04 OS.

Lets execute this container with singularity:

```bash
[ik1147@log-2 ~]$ singularity exec /scratch/work/public/singularity/cuda10.1-cudnn7-devel-ubuntu18.04-20201207.sif /bin/bash
Singularity> uname -a
Linux log-2.nyu.cluster 4.18.0-193.28.1.el8_2.x86_64 #1 SMP Fri Oct 16 13:38:49 EDT 2020 x86_64 x86_64 x86_64 GNU/Linux
Singularity> lsb_release -a
LSB Version:    core-9.20170808ubuntu1-noarch:security-9.20170808ubuntu1-noarch
Distributor ID: Ubuntu
Description:    Ubuntu 18.04.5 LTS
Release:        18.04
Codename:       bionic
```

Notice that we are still on the login node but within the Ubuntu container!

One can find more containers here:

`/scratch/work/public/singularity/`

Container files are read-only images, i.e. there is no need to copy over the container. Instead one may create a symlink for convenience. Please contact HPC if you need a container image with some specific software.

### Setting up an overlay filesystem with your computing environment

**Why?** The whole reason of using Singularity with overlay filesystem is *to reduce the impact on scratch filesystem* (remember how slow is it on Prince sometimes?). 

**High-level idea**: make a read-only filesystem which will be used exclusively to host your conda environment and other static files which you constantly re-use for each job.

**How is it different from scratch?** overlayfs is a separate fs mounted on each compute node when you start the container while scratch is a shared GPFS accessed via network.

There are two different modes when mounting the overlayfs:
* read-write: use this one when setting up env (installing conda, libs, other static files)
* read-only: use this one when running your jobs. It has to be read-only since multiple processes will access the same image. It will crash if any job has already mounted it as read-write.

Setting up your fs image:
1. Copy the empty fs gzip to your scratch path (e.g. `/scratch/<NETID>/` or `$SCRATCH` for your root scratch): `cp /scratch/work/public/overlay-fs-ext3/overlay-50G-10M.ext3.gz $SCRATCH/`
2. Unzip the archive: `gunzip -v $SCRATCH/overlay-50G-10M.ext3.gz` (can take a while to unzip...)
3. Execute container with overlayfs (check comment below about `rw` arg): `singularity exec --overlay $SCRATCH/overlay-50G-10M.ext3:rw /scratch/work/public/singularity/cuda10.1-cudnn7-devel-ubuntu18.04-20201207.sif /bin/bash`
4. Check file systems: `df -h`. There will be a record: `overlay          53G   52M   50G   1% /`. The size equals to the filesystem image you chose. **The actual content of the image is mounted in `/ext3`.**
5. Create a file in overlayfs: `touch /ext3/testfile`
6. Exit from Singularity

One has permission for file creation since the fs was mounted with `rw` arg. In contrast `ro` will mount it as read-only. 

Setting up conda environment:

1. Start a CPU (GPU if you want/need) job: `srun --nodes=1 --tasks-per-node=1 --cpus-per-task=1 --mem=32GB --time=1:00:00 --gres=gpu:1 --pty /bin/bash`
2. Start singularity (notice `--nv` for GPU propagation): `singularity exec --nv --overlay $SCRATCH/overlay-50G-10M.ext3:rw /scratch/work/public/singularity/cuda10.1-cudnn7-devel-ubuntu18.04-20201207.sif /bin/bash`
3. Install your conda env in `/ext3`: https://github.com/nyu-dl/cluster-support/tree/master/cassio#conda-environment.
    3.1. `wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh`
    3.2. `bash ./Miniconda3-latest-Linux-x86_64.sh -b -p /ext3/miniconda3`
    3.3. Install packages you are using (torch, jupyter, tensorflow etc.)
4. Exit singularity container (*not the CPU/GPU job*)

By now you have a working conda environment located in a ext3 image filesystem here: `$SCRATCH/overlay-50G-10M.ext3`. 

Let's run the container with **read-only** layerfs now (notice `ro` arg there):
`singularity exec --nv --overlay $SCRATCH/overlay-50G-10M.ext3:ro /scratch/work/public/singularity/cuda10.1-cudnn7-devel-ubuntu18.04-20201207.sif /bin/bash`

```bash
Singularity> conda activate
(base) Singularity> python
Python 3.8.5 (default, Sep  4 2020, 07:30:14)
[GCC 7.3.0] :: Anaconda, Inc. on linux
Type "help", "copyright", "credits" or "license" for more information.
>>> import torch
>>> torch.__version__
'1.7.0'
>>>
(base) Singularity> touch /ext3/test.txt
touch: cannot touch '/ext3/test.txt': Read-only file system
```

As shown above, the conda env works fine while `/ext3` is not writable.

**Caution:** by default conda and python keep cache in home: `~/.conda`, `~/.cache`. Since home fs has small quota, move your cache folder to scratch:
1. `mkdir $SCRATCH/python_cache`
2. `cd`
3. `ln -s $SCRATCH/python_cache/.cache`

```
.cache -> /scratch/ik1147/cache/
```

***From now on you may run your interactive coding/debugging sessions, congratulations!***

## Running a batch job with Singularity

files to use:
* `gpu_job.slurm`
* `test_gpu.py`

There is one major detail with a batch job submission: sbatch script starts the singularity container with a `/bin/bash -c "<COMMAND>"` tail, where `"<COMMAND>"` is whatever your job is running.

In addition, conda has to be sourced and activated. 

Lets create helper script for conda activation: copy the code below in `/ext3/env.sh`

```bash=
#!/bin/bash

source /ext3/miniconda3/etc/profile.d/conda.sh
export PATH=/ext3/miniconda3/bin:$PATH
```

This is an example batch job submission script (also as a file `gpu_job.slurm` in this repo folder):

```bash=
#!/bin/bash
#SBATCH --job-name=job_wgpu
#SBATCH --open-mode=append
#SBATCH --output=./%j_%x.out
#SBATCH --error=./%j_%x.err
#SBATCH --export=ALL
#SBATCH --time=00:10:00
#SBATCH --gres=gpu:1
#SBATCH --mem=64G
#SBATCH -c 4

singularity exec --nv --overlay $SCRATCH/overlay-50G-10M.ext3:ro /scratch/work/public/singularity/cuda10.1-cudnn7-devel-ubuntu18.04-20201207.sif /bin/bash -c "

source /ext3/env.sh
conda activate

python ./test_gpu.py
"
```

the output:
```
Torch cuda available: True
GPU name: Quadro RTX 8000


CPU matmul elapsed: 0.438138484954834 sec.
GPU matmul elapsed: 0.2669832706451416 sec.
```

***From now on you may run your experiments as a batch job, congratulations!***


## Setting up a simple sweep over a hyper-parameter using Slurm array job

files to use:
* `sweep_job.slurm`
* `test_sweep.py`

Usually we may want to do multiple runs of the same job using different hyper params or learning rates etc. There are many cool frameworks to do that like Pytorch Lightning etc. Now we will look on the simplest (imo) version of such sweep construction.

**High-level idea:** define a sweep over needed arguments and create a product as a list of all possible combinations (check `test_sweep.py` for details). In the end a specific config is mapped to its position in the list. The SLURM array id is used as a map to specific config in the sweep (check `sweep_job.slurm`).

Notes:
* notice no `--nv` in singularity call because we allocate CPU-only resources.
* notice `$SLURM_ARRAY_TASK_ID`. For each specific step job (in range `#SBATCH --array=1-20`) this env var will have the corresponding value assigned.

Submitting a sweep job:
`sbatch sweep_job.slurm`

Outputs from all completed jobs:
```
cat *out
{'sweep_step': 20, 'seed': 682, 'device': 'cpu', 'lr': 0.01, 'model_size': 1024, 'some_fixed_arg': 0}
{'sweep_step': 1, 'seed': 936, 'device': 'cpu', 'lr': 0.1, 'model_size': 512, 'some_fixed_arg': 0}
{'sweep_step': 2, 'seed': 492, 'device': 'cpu', 'lr': 0.1, 'model_size': 512, 'some_fixed_arg': 0}
{'sweep_step': 3, 'seed': 52, 'device': 'cpu', 'lr': 0.1, 'model_size': 512, 'some_fixed_arg': 0}
{'sweep_step': 4, 'seed': 691, 'device': 'cpu', 'lr': 0.1, 'model_size': 512, 'some_fixed_arg': 0}
{'sweep_step': 5, 'seed': 826, 'device': 'cpu', 'lr': 0.1, 'model_size': 512, 'some_fixed_arg': 0}
{'sweep_step': 6, 'seed': 152, 'device': 'cpu', 'lr': 0.1, 'model_size': 1024, 'some_fixed_arg': 0}
{'sweep_step': 7, 'seed': 626, 'device': 'cpu', 'lr': 0.1, 'model_size': 1024, 'some_fixed_arg': 0}
{'sweep_step': 8, 'seed': 495, 'device': 'cpu', 'lr': 0.1, 'model_size': 1024, 'some_fixed_arg': 0}
{'sweep_step': 9, 'seed': 703, 'device': 'cpu', 'lr': 0.1, 'model_size': 1024, 'some_fixed_arg': 0}
{'sweep_step': 10, 'seed': 911, 'device': 'cpu', 'lr': 0.1, 'model_size': 1024, 'some_fixed_arg': 0}
{'sweep_step': 11, 'seed': 362, 'device': 'cpu', 'lr': 0.01, 'model_size': 512, 'some_fixed_arg': 0}
{'sweep_step': 12, 'seed': 481, 'device': 'cpu', 'lr': 0.01, 'model_size': 512, 'some_fixed_arg': 0}
{'sweep_step': 13, 'seed': 618, 'device': 'cpu', 'lr': 0.01, 'model_size': 512, 'some_fixed_arg': 0}
{'sweep_step': 14, 'seed': 449, 'device': 'cpu', 'lr': 0.01, 'model_size': 512, 'some_fixed_arg': 0}
{'sweep_step': 15, 'seed': 840, 'device': 'cpu', 'lr': 0.01, 'model_size': 512, 'some_fixed_arg': 0}
{'sweep_step': 16, 'seed': 304, 'device': 'cpu', 'lr': 0.01, 'model_size': 1024, 'some_fixed_arg': 0}
{'sweep_step': 17, 'seed': 499, 'device': 'cpu', 'lr': 0.01, 'model_size': 1024, 'some_fixed_arg': 0}
{'sweep_step': 18, 'seed': 429, 'device': 'cpu', 'lr': 0.01, 'model_size': 1024, 'some_fixed_arg': 0}
{'sweep_step': 19, 'seed': 932, 'device': 'cpu', 'lr': 0.01, 'model_size': 1024, 'some_fixed_arg': 0}
```

**Caution:** be careful with checkpointing when running a sweep. Make sure that your checkpoints/logs have corresponding sweep step in the filename or so (to avoid file clashes).

***From now on you may run your own sweeps, congratulations!***

## Port forwarding to Jupyter Lab

### Part 1: launching JupyterLab on Greene.

1. Launch interactive job with a gpu: `srun --nodes=1 --tasks-per-node=1 --cpus-per-task=1 --mem=32GB --time=1:00:00 --gres=gpu:1 --pty /bin/bash`
2. Execute singularity container: `singularity exec --nv --overlay $SCRATCH/overlay-50G-10M.ext3:ro /scratch/work/public/singularity/cuda10.1-cudnn7-devel-ubuntu18.04-20201207.sif /bin/bash`
3. Activate conda (base env in this case): `conda activate`
4. Start jupyter lab: `jupyter lab --ip 0.0.0.0 --port 8965 --no-browser`

Expected output:

```
[I 15:51:47.644 LabApp] JupyterLab extension loaded from /ext3/miniconda3/lib/python3.8/site-packages/jupyterlab
[I 15:51:47.644 LabApp] JupyterLab application directory is /ext3/miniconda3/share/jupyter/lab
[I 15:51:47.646 LabApp] Serving notebooks from local directory: /home/ik1147
[I 15:51:47.646 LabApp] Jupyter Notebook 6.1.4 is running at:
[I 15:51:47.646 LabApp] http://gr031.nyu.cluster:8965/
[I 15:51:47.646 LabApp] Use Control-C to stop this server and shut down all kernels (twice to skip confirmation).
```

Note the hostname of the node we run from here: `http://gr031.nyu.cluster:8965/`

### Part 2: Forwarding the connection from you local client to Greene.

[Check here the ssh config](https://github.com/nyu-dl/cluster-support/blob/master/client/config) with the greene host to make the port forwarding easier to setup.

To start the tunnel, run: `ssh -L 8965:gr031.nyu.cluster:8965 greene -N`

**Note the hostname should be equal to the node where jupyter is running. Same with the port.**

Press Ctrl-C if you want to stop the port forwarding SSH connection.

***From now on you may run your own Jupyter Lab with RTX8000/V100, congratulations!***
