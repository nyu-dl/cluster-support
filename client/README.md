# Client setup

We define client as your own machine (PC, laptop etc.) which has a terminal with CLI and
SSH client.

You should be fine using any operating system as long as you are comfortable with it.

### MacOS, Linux
SSH client should be ready to be used by default.

### Windows 10
If you are using Windows 10, there are many options which you can google about, we highlight some of them here:

1. OpenSSH installed natively on Windows 10: [learn more](https://docs.microsoft.com/en-us/windows-server/administration/openssh/openssh_overview)

2. Windows Subsystem for Linux (this way you get linux shell with some limitations): [learn more](https://docs.microsoft.com/en-us/windows/wsl/install-win10)

3. Third-party software with SSH functionality (e.g. PuTTY): [learn more](https://www.putty.org/)

## Pre-requisites for tutorial:

* Make sure you have OpenSSH installed: commands `ssh`, `ssh-keygen` should work!

* Create SSH keypair: [learn more](https://www.ssh.com/ssh/keygen/)

* Make sure your `~/.ssh` folder exists and it  has correct system permissions: [learn more](https://wiki.ruanbekker.com/index.php/Linux_SSH_Directory_Permissions)

* Make sure you can connect to both CIMS access nodes and Prince login nodes: [CIMS](https://cims.nyu.edu/webapps/content/systems/userservices/netaccess/secure) [Prince](https://sites.google.com/a/nyu.edu/nyu-hpc/documentation/hpc-access)

*We will not spend time on these pre-requisites during the tutorial*

## NYU MFA

You should be aware of NYU multi-factor authentication already (which is used when you login to NYU services).

CIMS uses MFA authorization when you connect to access node via SSH. Follow necessary steps to login.

### Using ssh key instead of MFA

In order to login to access node without using MFA, append your public ssh key in `~/.ssh/authorized_keys_access` **ON ACCESS NODE** (create this file if needed). Set 600 permission mask to that file: `chmod 600 ~/.ssh/authorized_keys_access`.

## Creating SSH config file

SSH config is used to simplify ssh connection's configuration (such as usernames, ssh-key paths etc).

Make necessary edits to `config` file in current folder and copy it to `~/.ssh/config`.

After this step you should be able to directly connect to cassio host by typing `ssh cassio` or to access node via `ssh cims`.
