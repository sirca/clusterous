# Clusterous changelog 

## Version 1.0.0

Clusterous has reach its most stable version. It has been tested thoroughly on differents scenarios.


## Version 0.6.0

This version has a number of bug fixes.

* Updated documentation
* Updated PyGPlates enviroment
* Making output messages consistent
* Published package to PyPi
* Fixed IPython parallel enviroment example
* Fixed the shared volume deletion
* Fixed port forwarding issue on controller
* Fixed intermitent cluster creation failure


## Version 0.5.0

This version has a number of improvements and bug fixes. A notable feature is the setup wizard, which interactively guides you through configuring Clusterous. Additionally, there is a working Spark example environment and support for running in other AWS regions.

Note that there are some minor breaks in compatibility. The "Upgrading" section below will talk about the changes required to your environment files, etc.

### Changes

* New setup wizard to make it easier for first time users to get up and running. This is accessed via the `setup` command
* Support for managing multiple configurations - e.g. for different AWS regions or accounts
* Support for all AWS regions (except Seoul for now)
* Spark support and an example Spark environment
* Support for ports mappings from 1024 to 65535 in environment files
* Changes to environment file format: expose_tunnel is more flexible, support for Docker "host" networking
* Cluster now has a dedicated NAT, and all instances run an officially supported Ubuntu release - meaning better security and scaling
* Generally improved error handling
* Some small bugfixes
 
[README.md](https://github.com/sirca/bdkd_cluster/blob/master/README.md) and the [environment file documentation](https://github.com/sirca/clusterous/blob/master/docs/environment_file.md) have complete information on all new functionality.

## Upgrading

### Preparing
First, shut down any running clusters that were created with an earlier version using the `destroy` command. The new version of Clusterous will not work with clusters created by an earlier version.

```shell
$ clusterous destroy
```
Then uninstall the existing version of Clusterous:

```shell
$ pip freeze | grep clusterous
$ pip uninstall clusterous
```

### Install
Install the new version of Clusterous as per the instructions in [README.md](https://github.com/sirca/bdkd_cluster/blob/master/README.md).

Note that if you installed from source by checking out the code and using setup.py, the uninstallation procedure will be different.

**Important**: Before proceeding to use Clusterous, read the following sections on the changes you may need to make.

### Reconfigure Clusterous
Before running the new version, you need to update the configuration using the `setup` command. In earlier versions of Clusterous, it was necessary to manually create the ~/.clusterous.yml file. The new version of Clusterous will not work with the old, manually created configuration files. Instead, you need to recreate the configuration:

1. Create a backup copy of your ~/.clusterous.yml file and delete ~/.clusterous.yml
2. Run `clusterous setup`
3. Follow the guided steps, and where necessary, refer to your original config file for information on your keys, VPC, etc.
4. When prompted, give your created configuration a short name (e.g. 'myproject-sydney' if you use the Sydney AWS region)
 
You may then use `clusterous profile ls` and `clusterous profile show` to verify your new configuration.

The new configuration format was necessary to enable the setup wizard and support multiple profiles. With the `setup` and `profile` commands, you should not normally need to edit the ~/.clusterous.yml file.

### Change in terminology
In previous versions of Clusterous, the file in which you put cluster parameters (such as the number and types of instances) was refered to as the "profile" file. This file is now refered to as the "cluster" file, which better reflects its role in creating a new cluster. You still use the cluster file in the same way, with the `create` command.

The term "profile" now means something else. Clusterous now supports creating and managing multiple AWS configurations, each of which is refered to as a "profile". You may have a different profile for different AWS regions, or for different accounts. These can be managed by the new `profile` command. Use the `setup` command to create a new configuration profile.

### Change cluster file
Update your cluster file and replace `instance_count` with `worker_count`. In cluster files that use the default cluster, the `instance_count` field is gone and instead there is the `worker_count` field, with a slightly different meaning. The `instance_count` referred to the total number of instances, including the master. The less ambigious `worker_count` field only refers to the number of workers (there is always only 1 master). Change `instance_count` to `worker_count` in all your cluster files (née profile files) and reduce the number by 1.

### Update environment file
In your environment file(s), change the `expose_tunnel` section to display the URL correctly. In earlier versions of Clusterous, a URL would always be printed after the `expose_tunnel` message was displayed. Now, in order to have the URL displayed, you need to put the special `{url}` directive in the message. Clusterous also supports `{port}` to display only the port of the tunnel. Refer to the [environment file documentation](https://github.com/sirca/clusterous/blob/master/docs/environment_file.md) for full details.


## Version 0.4.1

### Improvements
* Documentation and licensing has been update

### Bugfix:
* On installation explicitly use python2

 
## Version 0.4.0

This version has a number of refinements and bug fixes and adds the ability to use your own EBS volume as the cluster's shared volume.

The most immediately obvious change is that the some command names have changed. Instead of using "start" and "terminate" to create and destroy a cluster, you now use "create" and "destroy" to do the same. Additionally, instead of using "launch" and "destroy" for environments, you now use "run" and "quit".

### Improvements
* Bring your own shared volume: you can have your cluster use your own EBS volume as the shared volume
* When terminating the cluster, you can chose to not delete the shared volume and then reuse it on another cluster
* Improved validation and error checking. Clusterous now checks for more types of errors in environment and profile files, and gives clear error messages
* Status command has been overhauled: nodes and running applications now listed in easy to understand form
* Some of the command names have been changed to reduce confusing between "terminate" and "destroy". You now "create" and "destroy" a cluster and "run" and "quit" an environment

## Upgrading

Clusterous 0.4.0 is not compatible with clusters created with an older version of Clusterous. Before installing the new version, terminate any existing clusters using the `terminate` command. The following are the steps to take:

#### 1. Terminate any existing cluster

```shell
$ clusterous status
$ clusterous terminate
```

#### 2. Uninstall existing version

```shell
$ pip freeze | grep clusterous
$ pip uninstall clusterous
```

(note that if you installed from source by checking out the code and using setup.py, the uninstallation procedure will be different)

#### 3. Install new version

Full instructions in [README.md](https://github.com/sirca/bdkd_cluster/blob/master/README.md)

#### 4. Note the new command names in v0.4.0

```shell
$ clusterous --version
$ clusterous --help
```

Make sure to use the new `create` command (instead of `start`) to create your cluster.


## Version 0.3.1

### Bugfix:
* Fixed installation issue when using pip

## 0.3.0

### New Features:
* Connect (SSH) to a running docker container
* Central logging system
* Add nodes to the cluster
* Remove nodes from the cluster
* Advanced cluster architectures, with multiple node groups

### Enhancements:
* Support for launching environment on cluster start up
* Custom size for shared volume
* Custom instance type for Controller
* Faster cluster start up (from 12 to 6 minutes)

### Upgrade from v0.2 to v0.3:
1.- Terminate running cluster

```shell
clusterous status
clusterous terminate
```

2.- Uninstall v0.2

```shell
pip freeze |grep clusterous
pip uninstall clusterous
```

3.- Install v0.3

[README.md](https://github.com/sirca/bdkd_cluster/blob/master/README.md)

4.- Update profile file

Old profile:
```yaml
- IPython:
    cluster_name: testcluster
    num_instances: 4
    instance_type: t2.micro
```

New profile:

```yaml
cluster_name: testcluster
#central_logging_level: 2
#environment_file: your-enviroment-file.yml
#shared_volume_size: 40 #GB
#controller_instance_type: c3.large
parameters:
    master_instance_type: t2.micro
    worker_instance_type: t2.micro
    instance_count: 2
```

5.- Create new cluster

You are ready to start using new features and enhancements of this release.


## 0.2.0

We are happy to announce the availability of Clusterous 0.2.0!

Clusterous 0.2.0 provides enough features to start a cluster (AWS only), run your Docker based application on the cluster and terminate the cluster. Additional features include uploading and downloading files, building Docker images, and viewing the status of the running cluster.


## 0.1.0

First release (internal only)
