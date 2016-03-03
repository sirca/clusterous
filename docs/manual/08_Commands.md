# Commands
Clusterous is a command line tool to manage virtual machines on Amazon Web Services (AWS).

## Synopsis
`` clusterous [options] <command> [<subcommand>] [parameters]``

Optonal parameters are shown in square brackets.

### Options
``--help``: Provides information about Clusterous commands.

``--verbose``: Displays verbose debug output while running the requested command.

``--version``: Displays the version Clusterous.

### Configuration related
Commands related to Clusterous configuration.

##### ``clusterous setup``

Launches an interactive wizard to configure Clusterous.

Example:
```
$ clusterous setup
Welcome to Clusterous setup
    This guide will help you create a new configuration profile for
    using Clusterous with Amazon Web Services

    Clusterous needs your AWS account's access keys
* AWS Access Key ID: _
```
---
##### ``clusterous profile``

List, switch between, show or remove configuration profiles
```
$ clusterous profile --help
usage: clusterous profile [-h] {rm,use,ls,show} ...
subcommands:
    ls              Show list of current profiles
    use             Switch to using another profile
    show            Show contents of a profile
    rm              Remove a profil
```

Example:
```
$ clusterous profile ls
Current Profile: default

Other Profiles
us-east-1
```

---
### Cluster related
Commands related to cluster management.

##### ``clusterous create``

Creates a cluster and run any specified environment.

```
$ clusterous create --help
arguments:
  profile_file  File containing cluster creation parameters

optional arguments:
  --no-run      Do not run environment
```

Example:
```
$ cat mycluster.yml
cluster_name: mycluster
parameters:
    master_instance_type: t2.micro
    worker_instance_type: t2.micro
    worker_count: 2

$ clusterous create mycluster.yml
Using profile default
Creating cluster...
...
```

---

##### ``clusterous status``

##### ``clusterous workon``

##### ``clusterous add-nodes``

##### ``clusterous rm-nodes``

##### ``clusterous destroy``

### Enviroment related
##### ``clusterous run``

##### ``clusterous connect``

##### ``clusterous quit``

### Files related
##### ``clusterous ls``

##### ``clusterous put``

##### ``clusterous get``

##### ``clusterous rm``

### Share volume related
##### ``clusterous ls-volumes``

##### ``clusterous rm-volume``

### Docker images related
##### ``clusterous build-image``

##### ``clusterous image-info``

### Central logging related
##### ``clusterous logging``
