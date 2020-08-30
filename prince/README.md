# NYU HPC Prince cluster

Troubleshooting: hpc@nyu.edu

NYU HPC website: [https://sites.google.com/a/nyu.edu/nyu-hpc/](https://sites.google.com/a/nyu.edu/nyu-hpc/)

One can find many useful tips under *DOCUMENTATION / GUIDES*.

In this part we will touch the following aspects of our own cluster:

* Connecting to Prince via CIMS Access

* Prince computing nodes

* Prince filesystems

* Software management

* Slurm Workload Manager

## Connecting to Prince via CIMS Access (without bastion HPC nodes)

HPC login nodes are reachable from CIMS access node, i.e. there is no need to login over another firewalled bastion HPC node. One can find corresponding `prince` block in the ssh config file (check client folder in this repo).

## Prince computing nodes

Learn more here: [https://sites.google.com/a/nyu.edu/nyu-hpc/systems/prince](https://sites.google.com/a/nyu.edu/nyu-hpc/systems/prince)

## Prince filesystems

Learn more here: [https://sites.google.com/a/nyu.edu/nyu-hpc/documentation/data-management/prince-data](https://sites.google.com/a/nyu.edu/nyu-hpc/documentation/data-management/prince-data)

## Software management

There is similar environment modules package as in Cassio for general libs/software.

There is no difference with managing **conda** on Cassio and on Prince except for installation path.

Learn more here: [https://sites.google.com/a/nyu.edu/nyu-hpc/documentation/prince/packages/conda-environments](https://sites.google.com/a/nyu.edu/nyu-hpc/documentation/prince/packages/conda-environments)

## Slurm Workload Manager

In general, Slurm behaves similarly on both Cassio and Prince, however there are differences in quotas and how GPU-equipped nodes are distributed:s

1. **There is no interactive QoS on Prince.** In other words, run `srun --pty bash` with additional args to get an interactive job allocated.

2. **There is no `--constraint` arg to specify a GPU you want.** 

    Instead, GPU nodes are separated into differnt **partitions** w.r.t. GPU type. Right now there are following parititons available: `--partition=k80_4,k80_8,p40_4,p100_4,v100_sxm2_4,v100_pci_2,dgx1,p1080_4`. Slurm will try to allocate nodes in the order given by this line. 

     |GPU|Memory|
     |---|------|
     |96 P40|24G|
     |32 P100|16G|
     |50 K80|24G bridged over 2 GPUs or 12G each|
     |26 V100|16G|
     |16 P1080|8G|
     |DGX1|16G ?|

### Port forwarding to interactive job

If one follows exactly same steps as for Cassio and run:

`ssh -L <port>:localhost:<port> -J prince <hpc_username>:<interactive_host>`

then the following error may be returned:

```
channel 0: open failed: administratively prohibited: open failed
stdio forwarding failed
kex_exchange_identification: Connection closed by remote host
```

which means that jump to your instance was not successful. In order to avoid this jump, we make a tunnel which will forward connection to the machine itself rather than localhost:

`ssh -L <port>:<interactive_host>:<port> prince -N`

**Important: you must run your JupyterLab or any other software with accepting requests from all ip addresses rather than from localhost only (which is a default usually).** To make this change in jupyter, add `--ip 0.0.0.0` arg:

`jupyter lab --no-browser --port <port> --ip 0.0.0.0`

Now you should be able to open JupyterLab tab in your browser.

### Submitting a batch job

As we noted before, one particular difference with Cassio is about GPU allocation (note `--partition` below):

```bash
#!/bin/bash
#SBATCH --job-name=<JOB_NAME>
#SBATCH --open-mode=append
#SBATCH --output=<OUTPUT_FILENAME>
#SBATCH --error=<ERR_FILENAME>
#SBATCH --export=ALL
#SBATCH --time=24:00:00
#SBATCH --partition=p40_4,p100_4,v100_sxm2_4,dgx1
#SBATCH --gres=gpu:1
#SBATCH --mem=64G
#SBATCH -c 4
```

**Important: do not forget to activate conda env before submitting a job, or make sure you do so in the script.**

Similar to arguments we passed to `srun` during interactive job request, here we specify requirements for the batch job.

After `#SBATCH` block one may execute any shell commands or run any script of your choice.

**You can not mix `#SBATCH` lines with other commands, Slurm will not register any `#SBATCH` after the first regular (non-comment) command in the script.**

To submit `job_wgpu` located in `gpu_job.slurm`, go to Cassio node and run:

`sbatch gpu_job.slurm`

sample output:

```
Torch cuda available: True
GPU name: Tesla V100-SXM2-32GB-LS


CPU matmul elapsed: 1.1984939575195312 sec.
GPU matmul elapsed: 0.01778721809387207 sec.
```
