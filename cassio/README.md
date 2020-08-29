# Cassio CILVR cluster

Troubleshooting: helpdesk@courant.nyu.edu

In this part we will touch the following aspects of our own cluster:

* CIMS computing nodes

* Courant / CILVR filesystems

* Software management

* Slurm Workload Manager

## CIMS computing nodes

Courant has their own park of machines which everyone is welcome to use, learn more about it [here](https://cims.nyu.edu/webapps/content/systems/resources/computeservers).
These machines do not have any workload manager.

## Filesystems

### Home filesystem

Everyone has their own home fs mounted in `/home/${USER}`.

Home fs has a limitation of 8GB (yes, eight) and one can check current usage with a command `showusage`:
```
[kulikov@cassio ~]$ showusage
You are using 56% of your 8.0G quota for /home/kulikov.
You are using 0% of your .4G quota for /web/kulikov.
```

There is a large benefit of using home fs: reliable backups. There are always 2 previous days backups of your fs located in `~/.zfs/`. In case if you can not locate the folder, fill a request [here](https://cims.nyu.edu/webapps/content/systems/forms/restore_file).

Home fs is a good place to keep important files such as project notes, code, experiment configurations.

### Big RAIDs

We have multiple big RAID filesystems, where one can keep checkpoints, datasets etc.

* `/misc/kcgscratch1`

* `/misc/vlgscratch4`

* `/misc/vlgscratch5`

We follow some simple folder structure as you will notice there.

Afaik there are no backups there, use `rm` very carefully.

### Transfer files

One can transfer some files to/from any location avaialable to your CIMS account via:

#### SSH (scp, rsync etc.)

Example command (assuming you have a working ssh config):

to cims:
`rsync -chaPvz <local_path> cims:<remote_path>`

from cims:
`rsync -chaPvz cims:<remote_path> <local_path>`

#### Using GLOBUS transfer service: [learn more](https://www.globus.org/)

**NYU HPC has disjoint filesystems from Courant/CILVR**

## Software management

**There is no sudo.** If you need to install some software (which is not possible to build locally), email helpdesk to assistance.

All computing machines including cassio node support dynamic modification of user's set of environment variables (`env`) which is called *environment modules* (learn more about it [here](http://modules.sourceforge.net/)).

Main command: `module`.

Why: imagine that we need to have all different versions of `gcc` installed on machines for various reasons. Every user can control what version of gcc to use via environment variable with the path to needed version.

Useful commands:

`module avail`: show all available modules to load

`module load <module_name>`

`module unload <module_name>`

`module purge`: unload all modules

Typical usecase: loading specific CUDA toolkit (with nvcc), gcc.

*Machine learning packages and libraries there are typically outdated.* Afaik it is a common practice to make your own python environment with either conda or embedded venv.

### Conda environment

Everyone has their own taste on how to build their DL/ML enviornment, here I will brifly discuss how to get Miniconda running. Miniconda ships just a python with a small set of packages + conda, while Anaconda is a monster.

Miniconda homepage: [https://docs.conda.io/en/latest/miniconda.html](https://docs.conda.io/en/latest/miniconda.html)

1. Copy the link to the install script in your clipboard and run: `wget <URL>` in the CIMS terminal.

There is no easy way to keep your conda env in home fs (8G quota), so type some location in your big RAID folder as installation path.

After installation type Y to agree to append neccessary lines into your `.bashrc`. After reconnection or re-login you should be able to run `conda` command.

2. Create conda env: `conda create -n tutorial python=3`. Activate tutorial env: `conda activate tutorial`.

3. Install several packages:

`conda install pytorch torchvision cudatoolkit=10.2 -c pytorch`

`conda install jupyterlab`

## Slurm Workload Manager
