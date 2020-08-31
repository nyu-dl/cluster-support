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

### Connecting between nodes once you are logged on Access node

Add your public key to `~/.ssh/authorized_keys` in order to jump between nodes without password typing each time. **Set restricted permissions on authorized_keys file**: `chmod 644 ~/.ssh/authorized_keys`.

## Filesystems

### Home filesystem

Everyone has their own home fs mounted in `/home/${USER}`.

Home fs has a limitation of 8GB (yes, eight) and one can check current usage with a command `showusage`:

```text
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

2. Create conda env: `conda create -n tutorial python=3`. Activate tutorial env: 

    `conda activate tutorial`

3. Install several packages:

`conda install pytorch torchvision cudatoolkit=10.2 -c pytorch`

`conda install jupyterlab`

## Slurm Workload Manager

### Terminal multiplexer / screen / tmux

Tmux or any other multiplexer helps you to run a shell session on Cassio (or any other) node which you can detach from and attach anytime later *without losing the state.*

Learn more about it here: [https://github.com/tmux/tmux/wiki](https://github.com/tmux/tmux/wiki)

### Slurm quotas

1. Hot season (conference deadlines, dense queue)

2. Cold season (summer, sparse queue)

### Cassio node

`cassio.cs.nyu.edu` is the head node from where one can submit a job or request some resources.

**Do not run any intensive jobs on cassio node.**

Popular job management commands:

`sinfo -o --long --Node --format="%.8N %.8T %.4c %.10m %.20f %.30G"` - shows all available nodes with corresponding GPUs installed. **Note features – this allows you to specify the desired GPU.**

`squeue -u ${USER}` - shows state of your jobs in the queue.

`scancel <jobid>` - cancel job with specified id. You can only cancel your own jobs.

`scancel -u ${USER}` - cancel *all* your current jobs, use this one very carefully.

`scancel --name myJobName` - cancel job given the job name.

`scontrol hold <jobid>` - hold pending job from being scheduled. This may be helpful if you noticed that some data/code/files are not ready yet for the particular job.

`scontrol release <jobid>` - release the job from hold.

`scontrol requeue <jobid>` - cancel and submit the job again.

### Running the interactive job

By interactive job we define a shell on a machine (possibly with a GPU) where you can interactively run/debug code or run some software e.g. JupyterLab or Tensorboard.

In order to request a machine and instantly (after Slurm assignment) connect to assigned machine, run:

`srun --qos=interactive --mem 16G --gres=gpu:1 --constraint=gpu_12gb --pty bash`

Explanation:

* `--qos=interactive` means your job will have a special QoS labeled 'interactive'. In our case this means your time limit will be longer than a usual job (7 days?), but there are max 2 jobs per user with such QoS.

* `--mem 16G` means the upper limit of RAM you expect your job to use. Machine will show all its RAM, however Slurm kills the job if it exceeds the requested RAM. **Do not set max possible RAM here, this may decrease your priority over time.** Instead, try to estimate the reasonable amount.

* `--gres=gpu:1` means number of gpus you will see in the requested instance. No gpus if you do not use this arg.

* `--constraint=gpu_12gb` each node has assigned features given what kind of GPU it has. Check `sinfo` command above to output all nodes with all possible features. Features may be combined using logical OR operator as `gpu_12gb|gpu_6gb`.

* `--pty bash` means that after connecting to the instance you will be given the bash shell.

You may remove `--qos` arg and run as many interactive jobs as you wish, if you need that.

#### Port forwarding from the client to Cassio node

As an example of port forwarding we will launch JupyterLab from interactive GPU job shell and connect to it from client browser.

1. Start an interactive job (you may exclude GPU to get it fast if your priority is low at the moment):

    `srun --qos=interactive --mem 16G --gres=gpu:1 --constraint=gpu_12gb --pty bash`

    Note the host name of the machine you got e.g. lion4 (will be needed for port forwarding).

2. Activate the conda environment with installed JupyterLab:

    `conda activate tutorial`

3. Start JupyterLab

    `jupyter lab --no-browser --port <port>`

    Explanation:

    * `--no-browser` means it will not invoke default OS browser (you don't want CLI browser).

    * `--port <port>` means the port JupyterLab will be listening for requests. Usually we choose some 4 digit number to make sure that we do not select any reserved ports like 80 or 443.

4. Open another tab on your terminal client and run:

    `ssh -L <port>:localhost:<port> -J cims <interactive_job_hostname> -N` (job hostname may be short e.g. lion4)

    Explanation:

    * `-L <port>:localhost:<port>` Specifies that the given port on the local (client) host is to be forwarded to the given host and port on the remote side.

    * `-J cims <other host>` means jump over cims to other host. This uses your ssh config to resolve what does cims mean.

    * `-N` means there will no shell given upon connection, only tunnel will be started.

5. Go to your browser and open `localhost:<port>`. You should be able to open JupyterLab page. It may ask you for security token: get it form stdout of interactive job instance.

**Disclaimer:** there are many other ways to get set this up: one may use ssh SOCKS proxy, initialize tunnel from the interactive job itself etc. And all the methods are OK if you can run it.

### Submitting a batch job

Batch jobs can be used for any computations where you do not expect your code to crash. In other words, there is no easy way to interrupt or debug running batch job.

Main command to submit a batch job: `sbatch <path_to_script>`.

The first part of the script consist of slurm preprocessing directives such as:

```bash
#SBATCH --job-name=job_wgpu
#SBATCH --open-mode=append
#SBATCH --output=./%j_%x.out
#SBATCH --error=./%j_%x.err
#SBATCH --export=ALL
#SBATCH --time=00:10:00
#SBATCH --gres=gpu:1
#SBATCH --constraint=gpu_12gb
#SBATCH --mem=64G
#SBATCH -c 4
```

**Important: do not forget to activate conda env before submitting a job, or make sure you do so in the script.**

Similar to arguments we passed to `srun` during interactive job request, here we specify requirements for the batch job.

After `#SBATCH` block one may execute any shell commands or run any script of your choice.

**You can not mix `#SBATCH` lines with other commands, Slurm will not register any `#SBATCH` after the first regular (non-comment) command in the script.**

To submit `job_wgpu` located in `gpu_job.slurm`, go to Cassio node and run:

`sbatch gpu_job.slurm`

#### What happens when you hit enter

Slurm registers your job in the database with corresponding job id. The allocation may not happen instantly and the job will be positioned in the queue.

One can get all available information about the job using:

`scontrol show jobid -dd <job_id>`

**One can only get information about pending or running job with the command above.**

While a job is in the queue, one can hold it from allocation (and later release) using corresponding commands we checked above.

### Managing experiments, running grid search etc

This is out of scope for today tutorial.
