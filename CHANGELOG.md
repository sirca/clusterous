# Clusterous

## 0.3.0

### New Features:
* Connect (SSH) to a running docker container
* Central logging system
* Add nodes to the cluster
* Remove nodes from the cluster

### Enhancements:
* Launch environment after cluster started: Start your cluster and launch your environment with one command.
* Custom instance type: Define your own instance types for your cluster
* Custom size for shared volume: Define the size for your shared volume
* Custom instance type for Controller: Bigger instance, faster building docker images
* Faster cluster start up: Reduced from 12 minutes to around 6 minutes

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
