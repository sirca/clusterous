# Shared Volume
This section tries to explain what is the shared volume on a Clusterous cluster, why it's important and how to manage it.

## What is it?

It is a [AWS EBS (SSD)](https://aws.amazon.com/ebs/details/) volume shared by NFS to all virtual machines on a Clusterous cluster. It is shared with full read and write access. It is mounted under the directory ```/home/data``` which can be accessed by your applications or using Clusterous commands explained further down in this section. Currently only one shared volume can be used on the cluster. The maximun size currently supported is 16TB. Using it incuress in AWS cost, more information you can find [here](https://aws.amazon.com/ebs/pricing/).

## What are the benefits of using it?
It allows you to store your data and perhaps your code on the cluster which can be used by your application. It could allow you to save results from your application and perhaps help you orquestrate a workflow in your application. You could keep this shared volume even after destroying your cluster so you could re-use it later when you create another cluster.

## How to create it?
Every Clusterous cluster has one shared volume wich is 20GB by default. You can specify a different size via ```shared_volume_size``` on your parameters file. In the example below we are requesting a 40GB shared volume:
```
$ cat mycluster.yml
cluster_name: mycluster
shared_volume_size: 40
parameters:
    master_instance_type: t2.micro
    worker_instance_type: t2.micro
    worker_count: 2
```
The creation of the shared volume happens at the creation of the cluster. Currently there is no support for attaching a shared volume to a running cluster.

## How to re-use it?
Clusterous allow you to re-use shared volumes that were created by Clusterous. It could be very useful if you have some data (perhaps large) that you want to process at different times by different clusters. In that scenario you transfer your data once to the shared volume spin up your first cluster, do you your processing, destroy the cluster and then re-use it later by a 2nd cluster and so on. In the following example we are requesting to re-use the volume ```vol-0266dac32```.
```
$ cat mycluster.yml
cluster_name: mycluster
shared_volume_id: vol-0266dac32
parameters:
    master_instance_type: t2.micro
    worker_instance_type: t2.micro
    worker_count: 2
```
Specified volume will be attached to the cluster at cluster creation. Currently there is no support for attaching a shared volume to a running cluster.

## How to use it?
* Clusterous provides the command ```put``` and ```get``` to transfer data/code in and out the cluster. The ```ls``` command to list the content of the shared volume. The ```rm``` command to delete folder on the shared volume. These command currently support folder level operations. 
* You could use the shared volume from your application which is under ```/home/data``` folder.
* You could ask Clusterous to transfer data from your computer to the cluster (see ```copy:``` entry in enviroment file) when you ```run``` your Clusterous environment.

## How to leve a shared volume for future use?
You could ask clusterous to keep the shared volume while destroying the cluster so you can re-use later.
You can do that by passing ```--force-delete-shared-volume``` as a parameter while you are destroying the cluster as shown in the example below:
```
$ clusterous destroy --force-delete-shared-volume
This will destroy the cluster mycluster. All data on the cluster will be deleted. Continue (y/n)? y
```

## How to see the list of shared volumes left by previous clusters?
Clusterous ```ls-volumes``` command allows you to see the list of shared volumes left by previous clusters (see example below). It is useful to know the volume ID so you can re-use it or perhaps delete it. This command shows only the volumes that were crated by Clusterous and currently are not attached to any running cluster.
```
$ clusterous ls-volumes
ID            Created                Size (GB)  Last attached to
vol-41978f85  2016-03-03 14:22:08           20  mycluster
vol-ed5e4429  2016-03-04 15:36:29           20  mycluster
```

## How to delete it?
Shared volumes are AWS EBS volumes and cost money (not much but nevertheless its money). Clusterous ```rm-volume``` command allows you to delete permanently the a volume as shown in the example below.
```
$ clusterous rm-volume vol-41978f85
This will delete shared volume "vol-41978f85". Continue (y/n)? y
Volume "vol-41978f85" has been deleted
```