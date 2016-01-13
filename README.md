# Clusterous
Clusterous is a general purpose tool for cluster computing on AWS. It allows you to create and manage a cluster on AWS and deploy your software in the form of Docker containers.

Clusterous is currently under active development. While it is currently usable, it should be regarded as pre-release software. The latest release is 0.4.1. 

Requires Linux or OS X and Python 2.7.

## About

Clusterous is being developed by [SIRCA](http://www.sirca.org.au/) as part of the Big Data Knowledge Discovery (BDKD) project funded by [SIEF](http://www.sief.org.au).

We are aiming to release a stable version 1.0 in Q1 2016. Leading up to the stable release we will be focusing on bugs, security, stability and platform support. We will also be adding some features and refining some existing functionality.

# Install

There are two ways to install Clusterous: either via pip, or by checking out the code from the git repository.


## Install via pip

To install Clusterous via pip, you need to obtain the .zip package file. A copy is available via the GitHub page under the 'releases' section (download one of the source code zip files). Then run the following on the command line:

    sudo pip install clusterous-v0.4.0.zip
    
Substitute `clusterous-v0.4.0.zip` with the exact file name.

### Note on Python versions
Clusterous is written in Python 2.7, and currently will not work under Python 3. If you are in an environment with Python 2.x and 3.x installed side-by-side, you have to ensure Clusterous is installed to work with the correct version of Python. Check which version of pip you have:

    pip --version
    
If it is the Python 3.x version, you will have to install the Python 2.x version of pip using your system's packaging tool. This version of pip can be run as `pip2`. You can verify this with:

    pip2 --version
    
Use `pip2` to install Clusterous.

## Install from source (alternative)

Alternatively, you may check out the Clusterous source and install from source. This method is recommended for advanced users, as uninstalling is slightly more complex. It is best done in a Python [virtualenv](https://virtualenv.pypa.io/en/latest/).


    git clone https://<username>@github.com/sirca/bdkd_cluster.git
    cd bdkd_cluster
    python setup.py develop

Note that you will have to ensure that Python 2.7 is used.
    
## Verify

To verify that Clusterous is installed, try:

    clusterous --help
    
And you should see Clusterous' help output.
    
    
## Configuring
Clusterous needs to be configured before it can be used. Create the file `.clusterous.yml` in your home directory. For example, if you use `vi`, you would type:

    vi ~/.clusterous.yml

A template of the contents of the file is as follows:
```yaml
- AWS:
    access_key_id: xxx
    secret_access_key: xxx
    key_pair: xxx
    key_file: xxx.pem
    vpc_id: vpc-xxx
    region: xxx
    clusterous_s3_bucket: xxx
```
Ensure that the key file is not readable by other users, or Clusterous will be unable to use it to connect to the virtual machines. A permissions mask of 600 is typical.

Add appropriate values for all fields. The `clusterous_s3_bucket` field takes the name of an S3 bucket that Clusterous uses for storing some data (currently just built Docker images). Just specify a name, and Clusterous will create a new bucket by that name. However, make sure you use a unique name that you can share with others in your organisation. For example `myorg-experiments-clusterous-bucket`, where `myorg` is the name of your organisation.

# Creating a cluster
To create a cluster, you need to provide Clusterous some information via a _profile file_. Create a file using a text editor. For example:

```
vi mycluster.yml
```

And add:

```yaml
cluster_name: mycluster
parameters:
    master_instance_type: t2.micro
    worker_instance_type: t2.micro
    worker_count: 2
```

Replace `mycluster` with any appropriate name for your cluster, ideally something unique to prevent a conflict with other Clusterous users on your AWS account. You can of course specify any instance types or number of workers. Note that by default you can only specify the number of worker nodes, as it doesn't make sense to have more than 1 "master" node in a master/worker architecture.

To create a cluster, type:

    clusterous create mycluster.yml
    

It will take several minutes to create the cluster. When the cluster has succesfully been created, you can run the `status` command to have a look:

    clusterous status
    
You will see some information about the cluster name, the number of instances running, etc.

You may terminate a cluster by using the `destroy` command (see below).

# Running an environment
In Clusterous, an `environment` refers to a Docker based application, along with any associated configuration and data. To run your application on a Clusterous cluster, you create an `environment file` containing instructions to run the application.

Detailed documentation for creating environment files is located under [docs/environment_file.md](https://github.com/sirca/bdkd_cluster/blob/master/docs/environment_file.md).

## IPython Parallel
As an example, the Clusterous source includes an IPython Parallel environment. The `run` command is used to launch an environment on a running cluster. Once the cluster is created, you can run IPython Parallel using the `ipython.yml` file located under `subprojects/environments/ipython-lite` in the Clusterous source. To launch, type the following (assuming you are in the bdkd_cluster root folder):

    clusterous run subprojects/environments/ipython-lite/ipython.yml
    
You will get detailed output as Clusterous starts up IPython Parallel. When you launch it for the first time (to be technical, for the first time with your configured S3 bucket), it takes some time to run as it builds an IPython Parallel Docker image. This built image is stored in the S3 bucket you specified in the configuration file.

Once it has run, Clusterous will output a URL to the IPython notebook on your cluster. Open this URL in your web browser to access the IPython notebook.

## Quiting the environment
If you want to run another environment on the cluster, or relaunch the current environment, you first need to stop the currently running one. Simply use:

    clusterous quit
    
And you will be prompted to confirm before clusterous stops the running containers. This command will not touch any of the data in the shared volume.

# Destroy the cluster
Once you are done, run the `destroy` subcommand to stop the cluster. This will remove all AWS resources that Clusterous created (with the exception of the Clusterous S3 bucket).

    clusterous destroy
    
# Adding and removing nodes
You can scale the number of nodes on a cluster using the `add-nodes` and `rm-nodes` commands. Any running application will also be scaled according the parameters specified in the application's environment file.

To add, say, 5 nodes of the default 'worker' type to the running cluster, just use:

    clusterous add-nodes 5
    
In more advanced clusters, there may be more than one type of scalable nodes - e.g. CPU workers and IO workers. Just specify the exact node type after the number.

Removing nodes is similarly simple; to remove 5 nodes, type:

    clusterous rm-nodes 5
    
Take care when removing nodes from a cluster with a running application.

# Advanced options

The profile file used to create a cluster has some advanced options. The following example enables some extra (optional) features:

```yaml
cluster_name: mycluster
environment_file: subprojects/environments/ipython-lite/ipython.yml
central_logging_level: 2
controller_instance_type: t2.medium
shared_volume_size: 60
parameters:
    master_instance_type: t2.micro
    worker_instance_type: t2.micro
    instance_count: 3
```

The `environment_file` field allows you to run your environment on cluster creation. Simply specify a relative (or absolute) path to the YAML environment file, and Clusterous will automatically run the environment after the cluster starts up. This avoids the need for running the `run` command separately.

The `central_logging_level` field enables the logging system, useful for debugging problems. The logging system consists of a special dedicated virtual machine in your cluster that collects log messages from the cluster and makes them accessing via a web GUI. The number refers to the logging level; `1` means that only application logs are collected (i.e. if your application logs via syslog), `2` additionally enables collection of logs from system services. To view the logs, use `clusterous logging`.

The `controller_instance_type` field allows you to specify a custom cluster type for the Controller, which is the dedicated Clusterous node manages the cluster. You may typically need a more powerful node if you are building very large Docker images on the cluster. On AWS, the default Controller type is a t2.small.

The `shared_volume_size` field lets you specify a custom size for the cluster shared volume in gigabytes (e.g. `60` means 60 GB). The default value is 20.


# Managing the shared volume

A Clusterous cluster has data volume that is shared between all the machines on the cluster. This volume is for use by cluster applications for their input and output data.

You can manage the files on this shared volume via the following commands

## Listing files

Simply use the `ls` commands to list the files on the shared volume

    clusterous ls
    
You may provide a parameter to list the files in a subdirectory. For example:

    clusterous ls main/dataset1/
    
## Syncing files to and from cluster

The `put` and `get` commands let you transfer files from your machine to the cluster and vice versa. Both commands use rsync underneath, meaning that only changes are transfered, making it very efficient when dealing with large amounts of data.

Note that the commands only work with entire directories at a time.

To transfer a directory named `main` from your local machine to the cluster, use:

    clusterous put main

You may confirm the transfer with `clusterous ls`.

To transfer a directory from the cluster to your local machine, use:

    clusterous get main
    
You can easily delete a directory on the shared volume via `rm`:

    clusterous rm main

## Custom shared volumes
By default, Clusterous creates a shared volume when creating the cluster. Alternatively, you may set the `shared_volume_id` field in the profile file to the id of an EBS volume you want to use as the shared volume. If this field is specified, Clusterous does not create a shared volume for the cluster; instead, the specified volume is mounted in the same way.

There are a couple of extra options related to custom shared volumes. When destroying a cluster, you may specify that the shared volume be left undeleted for use in another cluster. This can be useful if you want to avoid copying the data to your system and then copying it again to the shared volume of a new cluster. When issuing the `destroy` command, specify `--leave-shared-volume` to detach the shared volume before the cluster is terminated.

To list previously detached shared volumes, use the `ls-volumes` command. This command will only show volumes that were created by Clusterous:

    clusterous ls-volumes

To delete a detached volume that isn't needed any more, use the `rm-volume` command:

    clusterous rm-volume
    
Note that a given shared volume can only be attached to a single cluster at any time.

By default, when destroying a cluster that has a custom shared volume, the shared volume isn't automatically destroyed. Use the `--force-delete-shared-volume` argument of the `destroy` command to delete the custom shared volume when destroying the cluster.


# Other commands
## Set working cluster

When you (or your team) are running multiple clusters at once, you can switch between them using the `workon` command.

    clusterous workon testcluster

Note that Clusterous currently does not support creating more that one cluster from the same machine.


## Logging system

If the logging system is enabled (see section on advanced options), you can access the logs with the help of the `logging` command:

    clusterous logging
    
This command will create an SSH tunnel from your local machine to the logging instance on the cluster and will present you with a URL to access the logging system's web interface.

## Connecting to a container
When you have an environment running, you may connect to one of your containers' shell via the `connect` command. For example, if your environment has a 'master' component, you can use:

    clusterous connect master
    
Note that you are currently limited to connecting to containers that have only 1 instance.


## Building a Docker image on the cluster

While you make typically build any custom Docker image as a step in your environment file, you may also build one using the `build-image` command:

    
    clusterous build-image image_dir bdkd:sample_v1

The `image_dir` argument in the example is the directory containing a `Dockerfile`. The built container is stored in the private registry, and will be available to other clusters in your account.

## Get information about a Docker image

You may obtain information about a Docker image in your private registry:

    clusterous image-info bdkd:sample_v1
    
# Licensing
Clusterous is available under the Apache License (2.0). See the LICENSE.md file.

Copyright NICTA 2015.



