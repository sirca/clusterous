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

##### ``clusterous status``
Show information about the current cluster and any running application.

Example
```
$ clusterous status
mycluster has 5 instances running, including nat and controller
Uptime:		24 minutes

Controller
IP: 52.62.12.156  Port: 22000

Node Name     Instance Type      Count  Running Components
[controller]  t2.small               1  --
[nat]         t2.micro               1  --
worker        t2.micro               2  [None]
master        t2.micro               1  [None]

Shared Volume
44M (1%) used of 20G
19G available
```

##### ``clusterous workon``
Sets a working cluster. In the scenario that one of your colleges wants to use your cluster, He or She can run this command to use your cluster. Note that Clusterous currently does not support creating more that one cluster from the same machine.
```
$ clusterous workon --help
arguments:
  cluster_name  Name of the cluster
```

Example:
```
$ clusterous workon mycluster
Switched to mycluster
```

##### ``clusterous add-nodes``
Use this command to scale up the number of nodes on your cluster. Any running application will also be scaled accordingly.
```
$ clusterous add-nodes --help
arguments:
  num_nodes   Number of nodes to add
  node_name   Name of node type to add
```

Example:
```
$ clusterous status
...
Node Name     Instance Type      Count  Running Components
worker        t2.micro               2  engine
...

$ clusterous add-nodes 2 worker
Creating 2 "worker" nodes
Waiting for nodes to start...
Configuring nodes...
2 nodes of type "worker" added
Scaling running environment
Added 4 running instances of component "engine"

$ clusterous status
...
Node Name     Instance Type      Count  Running Components
worker        t2.micro               4  engine
...
```

##### ``clusterous rm-nodes``
Use this command to scale down the number of nodes on your cluster. Any running application will also be scaled accordingly.
```
$ clusterous rm-nodes --help
arguments:
  num_nodes   Number of nodes to remove
  node_name   Name of node type to remove
```

Examples:
```
$ clusterous status
...
Node Name     Instance Type      Count  Running Components
worker        t2.micro               4  engine
...

$ clusterous rm-nodes 1 worker
Removing 1 nodes of type "worker"...
1 nodes of type "worker" removed
Scaling running environment
Removed 2 running instances of component "engine"

$ clusterous status
...
Node Name     Instance Type      Count  Running Components
worker        t2.micro               3  engine
...
```

##### ``clusterous destroy``

### Enviroment related
In Clusterous, an environment refers to a Docker based application, along with any associated configuration and data. More information [here](../environment_file.md).

##### ``clusterous run``
```
$ clusterous run --help
arguments:
  environment_file      Enviroment file name in YML format
```
Example:
```
$ clusterous run my-env.yml
Checking for Docker images...
Copying files...
Starting 4 instances of engine
Starting 1 instance of master
Launched 2 components: master, engine

Message for user:
To access the master, use this URL: http://localhost:8888

$ clusterous status
...
Node Name     Instance Type      Count  Running Components
worker        t2.micro               2  engine
master        t2.micro               1  master
...
```

##### ``clusterous connect``
Connects to a running component (docker container) and gets an interactive shell. Use ```exit``` to exit from the interactive shell. It could be useful for debuging your application.
```
$ clusterous connect --help
arguments:
  component_name  Name of the component (see status command)
```
Example:
```
$ clusterous connect master
Connecting to 'master' component
root@7ef552e48227:/#
```

##### ``clusterous quit``
Stops any running application on the cluster and removes existing SSH tunnels from your computer to the application.
```
$ clusterous quit --help
arguments:
  --tunnel-only  Only remove any SSH tunnels, do not stop application
  --confirm      Immediately stops application without prompting for confirmation
```

Example:
```
$ clusterous quit
This will stop the running cluster application. Continue (y/n)? y
2 running applications successfully destroyed
```



### Share volume related
Each Clusterous cluster has its own shared volume, which is a virtual hard drive accessible to all machines via NFS. The following commands are related to this shared volume.

##### ``clusterous put``
Copies a folder from your computer to the shared volume on the cluster. Currently only folder livel is supported.
```
$ clusterous put --help
arguments:
  local_path   Path to the local folder
  remote_path  Path on the shared volume
```
Example:

Copies the folder ```~/tmp/cities``` from your computer to the shared volume on the cluster.
```
$ clusterous put ~/tmp/cities
```

##### ``clusterous ls``
List contents of the shared volume on the cluster.
```
$ clusterous ls --help
arguments:
  remote_path  Path on the shared volume
```
Example:

List the folder on the shared volume. If no ```remote_path``` is provided it shows the root directory of the shared volume.
```
$ clusterous ls
total 32
drwxr-xr-x 5 ubuntu ubuntu  4096 Mar  3 22:33 .
drwxr-xr-x 4 root   root    4096 Mar  3 03:24 ..
drwxr-xr-x 2 ubuntu ubuntu  4096 Feb 11 01:55 cities
...
```

##### ``clusterous get``
Copies a folder from the shared volume on cluster to your computer. Currently only folder livel is supported.
```
$ clusterous get --help
arguments:
  remote_path  Path on the shared volume
  local_path   Path to the local folder
```
Example:

Copies the folder ```cities``` from the shared volume on the cluster to your current folder on your computer.
```
$ clusterous get cities .
```

##### ``clusterous rm``
Deletes a folder from the shared volume on the cluster. Currently only folder livel is supported.
```
$ clusterous rm --help
arguments:
  remote_path  Path on the shared volume
```
Example:

Delete the folder ```cities``` from the shared volume on the cluster.
```
$ clusterous rm cities
```
##### ``clusterous ls-volumes``
List the shared volumes that were created by Clusterous at some point and were left for future use. The list shows only unattached shared volumes which means your current shared volume won't be included in the list. You may find it useful for reusing shared volumes from previous clusters.
```
$ clusterous ls-volumes --help
List unattached shared volumes left from previously destroyed clusters
...
```
Example:
```
$ clusterous ls-volumes
ID            Created                Size (GB)  Last attached to
vol-8e59004a  2016-01-08 10:41:21           20  basiccluster
vol-76280fb2  2016-01-13 11:26:01           40  customcluster
...
```


##### ``clusterous rm-volume``
Deletes an unattached shared volume created by Clusterous.
```
$ clusterous rm-volume --help
arguments:
  volume_id   Volume ID
```
Example:

Deleting the shared volume ```vol-8e59004a```.
```
$ clusterous rm-volume vol-8e59004a
This will delete shared volume "vol-8e59004a". Continue (y/n)? y
Volume "vol-8e59004a" has been deleted
```

### Docker images related
##### ``clusterous build-image``
Allows you to build your Docker image on the cluster to be used by your environment file later. Normally you don't need to run this command manually since the ```run``` command will do automatically for you. 
```
$ clusterous build-image --help
arguments:
  dockerfile_folder  Local folder name which contains the Dockerfile
  image_name         Name of the docker image to be created on the cluster
```

##### ``clusterous image-info``
Gets the information of a specified Docker image that exist on the cluster. Normally you don't need to run this command manually since the ```run``` command will check automatically if any Docker image you are trying to use exist otherwise it creates for you.
```
$ clusterous image-info --help
arguments:
  image_name  Name of the docker image available on the cluster
```

### Central logging related
##### ``clusterous logging``
This command will create an SSH tunnel from your compter to the central logging on the cluster and will present you with a URL to access the logging system's web interface. Remember this the central loging is optional, more information on it separete section of this manual.
```
$ clusterous logging --help
....
```

