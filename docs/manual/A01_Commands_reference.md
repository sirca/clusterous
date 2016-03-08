# Commands
Tool to create and manage compute clusters.

## Synopsis
`clusterous [options] <command> [<subcommand>] [parameters]`

Optional parameters are shown in square brackets.

### Options
`--help`: Provides information about Clusterous commands.

`--verbose`: Displays verbose debug output while running the requested command.

`--version`: Displays the version Clusterous.

### Configuration related
Commands related to Clusterous configuration.

##### `clusterous setup`
Launches an interactive wizard to configure Clusterous.

##### `clusterous profile`
Command to manage configuration profiles.

Sub-commands:
* `ls`: Show list of current profiles
* `use`: Switch to using another profile
* `show`: Show contents of a profile
* `rm`: Remove a profile

### Cluster related
Commands related to cluster management.

##### `clusterous create`
Creates a cluster and optionally runs an environment.

##### `clusterous status`
Show information about the current cluster and any running application.

##### `clusterous workon`
Sets a working cluster. In the scenario that one of your colleges wants to use your cluster, They can run this command to use your cluster. Note that Clusterous currently does not support creating more that one cluster from the same machine.

##### `clusterous add-nodes`
Use this command to scale up the number of nodes on your cluster. Any running application will also be scaled accordingly.

##### `clusterous rm-nodes`
Use this command to scale down the number of nodes on your cluster. Any running application will also be scaled accordingly.

##### `clusterous destroy`
Destroy the working cluster, removing all resources

### Enviroment related
In Clusterous, an environment refers to a Docker based application, along with any associated configuration and data. More information in the section [Environments](06_Environments.md)

##### `clusterous connect`
Connects to a running component (Docker container) and gets an interactive shell. Use `exit` to exit from the interactive shell. It could be useful for debuging your application.

##### `clusterous quit`
Stops any running application on the cluster and removes existing SSH tunnels from your computer to the application.

### Share volume related
Each Clusterous cluster has its own shared volume, which is a virtual hard drive accessible to all machines via NFS. 
More information about shared volume [here](07_Shared_volume.md).

### Docker images related
##### `clusterous build-image`
Allows you to build your Docker image on the cluster to be used by your environment file later. Normally you don't need to run this command manually since the `run` command will do automatically for you. 

##### `clusterous image-info`
Gets the information of a specified Docker image that exist on the cluster. Normally you don't need to run this command manually since the `run` command will check automatically if any Docker image you are trying to use exist otherwise it creates for you.

### Central logging related
##### `clusterous logging`
This command will create an SSH tunnel from your compter to the central logging on the cluster and will present you with a URL to access the logging system's web interface. Remember this the central loging is optional. More information about the central loging [here](07_Central_logging.md)

