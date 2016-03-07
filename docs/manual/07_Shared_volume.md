# Shared Volume
Every Clusterous cluster has a virtual hard drive accessible to all nodes via NFS. The shared volume can be used for storing your application's configuration, parameters, results, etc. 

## Background
Shared volumes use AWS' [Elastic Block Store (EBS)](https://aws.amazon.com/ebs/details/) feature and are configured during cluster creation. There are two ways to access the contents of shared volume:

- Via the cluster application: the shared volume is mounted on /home/data on all Docker containers running inside Clusterous
- Via the command line: Clusterous provides commands to list, copy and delete files on the shared volume

What you use the shared volume is up to you. Environments often use them to store configuration information that all nodes need to use. You may copy your application's input data to the shared volume such that all parts of your application can access the data. You may similarly use the shared volume for your application's output: simply copt the results back to your computer when your application is done.

By default, the shared volume is 20GB, and is created and destroyed along with the cluster it is tied to. However, Clusterous allows you to specify any size, and gives you to option of preserving a shared volume and using it later.

## Shared volume size
By default, the shared volume is 20GB. You may customise this at cluster creation via the `shared_volume_size` field in the cluster parameters file. The `shared_volume_size` accepts the size of the shared volume in gigabytes, and is outside the parameters section.

In the following cluster parameters file, we set the shared volume to 40GB:

```
cluster_name: mycluster
shared_volume_size: 40
parameters:
    master_instance_type: t2.micro
    worker_instance_type: t2.micro
    worker_count: 2
```

When you run `create` with the above parameters, the created cluster will have a new shared volume of 40GB. Note that the shared volume is always attached at cluster creation and Clusterous doesn't allow you to change the size after the cluster is created.

Clusterous currently uses "EBS Magnetic" storage for shared volumes, meaning that shared volumes can be up to 1TB in size.

## Accessing the shared volume on the command line
Clusterous provides 4 commands for accessing data on the shared volume: `ls`, `put`, `get` and `rm`. For each command, you may use `--help` to get detailed usage information, as per usual.

To view the contents of the shared volume, use the `ls` command:

```
$ clusterous ls
total 32
drwxr-xr-x 5 ubuntu ubuntu  4096 Mar  3 22:33 .
drwxr-xr-x 4 root   root    4096 Mar  3 03:24 ..
drwxr-xr-x 2 ubuntu ubuntu  4096 Feb 11 01:55 my_data
```

This shows the top level of the shared volume; you may also provide a path to `ls` to examine any directories:

```
$ clusterous ls my_data
total 17
drwxr-xr-x 5 ubuntu ubuntu  4096 Feb 11 01:55 .
drwxr-xr-x 4 ubuntu ubuntu  4096 Mar  3 22:33 ..
-rw-r--r-- 2 ubuntu ubuntu  4096 Feb 11 01:56 myfile.dat
```

To copy files to and from your location machine and the shared volume, use the `put` and `get` commands. Note that hese commands always work on the directory level, and currently do not support copying individual files.

For example to copy a directory called "cities" from your local machine to the top level of the shared volume, use:

```
$ clusterous put ~/cities
```

To copy it back (to the current directory):

```
$ clusterous get cities .
```

The `put` and `get` commands use rysnc internally, meaning that only the differences between files are copied. This ensures that small updates to big collections of data are efficient.

You may delete a directory on the shared volume using `rm`. For example:

```
$ clusterous rm cities
```

## Accessing the shared volume from the environment
The shared volume is mounted to `/home/data` on every container in the environment. The [environment files](06_Environments.md) chapter has more information on creating custom environments.

## Reusing shared volumes
Clusterous allows you to preserve a shared volume when you destroy a cluster, such that you can later reuse that volume for another cluster. This may be especially useful if you have a large amount of data, and do not want to spend time copying data back and forth between cluster runs.

First, to preserve the shared volume on cluster destruction, pass the `--leave-shared-volume` to the `destroy` command:
```
$ clusterous destroy --leave-shared-volume
```

You may then inspect detached shared volumes that are available on your account using the `ls-volumes` command. This command shows you all shared volumes that were created by Clusterous and currently available. It does not show volumes that are currently attached to a running cluster.

```
$ clusterous ls-volumes
ID            Created                Size (GB)  Last attached to
vol-12345667  2016-03-03 14:22:08           20  mycluster
vol-abc15325  2016-03-04 15:36:29           20  mycluster
```

To reuse one of the above volumes in a new cluster, you need to specify the volume ID in the cluster parameters file.

In the cluster parameters file, use the `shared_volume_id` field. For example, the below parameters file would attach the volume `vol-12345667` to the newly created cluster:

```
$ cat mycluster.yml
cluster_name: mycluster
shared_volume_id: vol-12345667
parameters:
    master_instance_type: t2.micro
    worker_instance_type: t2.micro
    worker_count: 2
```

If a cluster reuses a shared volume in this way, Clusterous will by default not delete the shared volume when the `destroy` command is run. To override this behaviour, and to delete the attached volume when the cluster is destroyed, use the `--force-delete-shared-volume` option.

The `shared_volume_id` can also be used to attach EBS volumes that haven't been created by Clusterous.

## Deleting the shared volume
To permanently delete a dettached shared volume that you no longer want to use, use the `rm-volume` command:

```
$ clusterous rm-volume vol-41978f85
This will delete shared volume "vol-41978f85". Continue (y/n)? y
Volume "vol-41978f85" has been deleted
```

This will let you manage costs, as AWS charges for EBS volumes even when they are not in use.