# Creating and Destroying clusters

Creating and destroying a Clusterous cluster is achieved via the `create` and `destroy` commands respectively. 

## `create`
When you run the `create` command, Clusterous creates a new cluster in AWS, as per the configuration you created with the `setup` command. After the `create` command finishes running, you will have a fully running and configured cluster on your AWS account. You can optionally also have the `create` command run your application immediately after the cluster is created.

The `create` command takes as input a .yml file with some basic parameters such as the number of virtual machine instances you want, the name of the cluster, and so on. This file, refered to as the cluster parameters file, also supports a number of additional options; these options are elaborated in this chapter.

Once you have created a cluster, that cluster is set as your working cluster. Since Clusterous "remembers" the cluster you have created, you do not have to specify the cluster name in any further commands. Until you `destroy` a cluster, any further cluster commands apply to the current working cluster.

## Cluster Parameters file
Clusterous' `create` command accepts cluster parameters in the [YAML](https://en.wikipedia.org/wiki/YAML) file format. YAML files (which have a .yml extension) are a way of representing structured data in a clean and human-readable format.

### Basics

A basic parameters file looks like this:

```yaml
cluster_name: mycluster
parameters:
    master_instance_type: t2.micro
    worker_instance_type: t2.micro
    worker_count: 2
```

This file will tell Clusterous to create a cluster named "mycluster". By default, the parameters section requires 3 fields: `master_instance_type`, `worker_instance_type`, `worker_count`, which describe the basic parameters of the default master/worker cluster.

`master_instance_type` and `worker_instance_type` are the AWS instance types that the master node and worker nodes (respectively) should be. These are the simple string values of AWS instance types, such as `t2.micro` or 'c4.large'. The master and workers may be of different types. However, the exact type you choose is up to you, and depends on the demands of your application.

Note that the types of instances cannot be changed once the cluster has been created.

The `worker_count` field is the number of worker nodes that should be created. In the default master/worker architecture, there is always only 1 master, and 1 or more workers. The number of workers can be changed after the cluster is created, with the `add-nodes` and `rm-nodes` commands.

Thus far, we have discussed the "default" architecture, consisting of 1 master and many workers. Clusterous also allows you to define a custom cluster architecture, which is described in the "Environments" chapter. If using a custom cluster architecture, all the fields under `parameters` will be different, as defined by the custom architecture.

### Advanced options
There are a number of advanced options when creating a cluster. The following example file uses some of these optional fields:

```yaml
cluster_name: mycluster
environment_file: demo/ipython-lite/ipython.yml
central_logging_level: 2
controller_instance_type: t2.medium
shared_volume_size: 60
shared_volume_id: vol-1251        # cannot be used if shared_volume_size is used
parameters:
    master_instance_type: t2.micro
    worker_instance_type: t2.micro
    worker_count: 3
```

The `environment_file` field allows you to run your environment on cluster creation. Simply specify a relative (or absolute) path to the YAML environment file, and Clusterous will automatically run the environment after the cluster starts up. This avoids the need for running the `run` command separately. Environments are described in full detail in [Chapter 6](06_Environments.md).

The `central_logging_level` field enables the logging system, useful for debugging problems. The logging system consists of a special dedicated virtual machine in your cluster that collects log messages from the cluster and makes them accessing via a web GUI. The number refers to the logging level; `1` means that only application logs are collected (i.e. if your application logs via syslog), `2` additionally enables collection of logs from system services. To view the logs, use `clusterous logging`. The logging system is described in detail in [Chapter 8](08_Central_logging.md).

The `controller_instance_type` field allows you to specify a custom cluster type for the Controller, which is the dedicated Clusterous node manages the cluster. You may typically need a more powerful node if you are building very large Docker images on the cluster. On AWS, the default Controller type is a t2.small.

The `shared_volume_size` field lets you specify a custom size for the cluster shared volume in gigabytes (e.g. `60` means 60 GB). The default value is 20.

The `shared_volume_id` field lets you specify a custom shared volume, instead of having Clusterous create a new one. This feature is described in detail in [Chapter 7](07_Shared_volume.md).

## `destroy`
The `destroy` command terminates all nodes in the cluster and cleans up the AWS resources created when the `create` command was run. By default, the shared volume is also destroyed, permanently deleting all files on it.

The `destroy` command also supports the `--leave-shared-volume` and `--force-delete-shared-volume` fields, which offer flexibility with the shared volume. These features are described in Chapter 6 [Chapter 7](07_Shared_volume.md).

## `workon`
Clusterous doesn't currently support working with and managing multiple clusters from the same machine. However, it is sometimes useful to be able to create a cluster using one machine and then work on it from a second machine.

Assuming that both machines are configured to use the same account and region, you can use `workon` to access the cluster from the second machine:

    clusterous workon mycluster

From then on, you can use cluster commands as per normal. Since the original machine will also have full access to the same cluster, be careful not to apply two conflicting commands at the same time.