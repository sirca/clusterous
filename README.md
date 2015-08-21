# Clusterous
Cluster compute tool for running Docker based applications on AWS.

Written in Python. Requires Linux or OS X.

## Install

Install Clusterous via pip.

    pip install clusterous_package.zip
    
Substitute `clusterous_package.zip` with the appropriate package name.

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
    subnet_id: subnet-xxx
    region: xxx
    clusterous_s3_bucket: xxx
```

Add appropriate values for all fields. The `clusterous_s3_bucket` field takes the name of an S3 bucket that Clusterous uses for storing some data (currently just built Docker images). Just specify a name, and Clusterous will create a new bucket by that name. However, make sure you use a unique name that you can share with others in your organisation. For example `myorg-experiments-clusterous-bucket`, where `myorg` is the name of your organisation.

## Starting a cluster
To start a cluster, you need to provide Clusterous some information via a _profile file_. Create a file using a text editor. For example:

```
vi mycluster.yml

```

And add:

```yaml
cluster_name: mycluster
parameters:
    master_instance_type: t2.micro
    worker_instance_type: t2.micro
    instance_count: 3
```

Replace `mycluster` with any appropriate name for your cluster, ideally something unique to prevent a conflict with other Clusterous users on your AWS account. You can of course specify any instance types or number of instances. Note that the number of instances includes the master (i.e. if you specify `instance_count` of 3, there will be 2 worker instances and 1 master instance).

To start a cluster, type:

    clusterous start mycluster.yml
    

It will take several minutes to start the cluster. When the cluster has succesfully been started, you can run the `status` command to have a look:

    clusterous status
    
You will see some information about the cluster name, the number of instances running, etc.

## Launching an environment
In Clusterous, an `environment` refers to a Docker based application, along with any associated configuration and data. To run your application on a Clusterous cluster, you create an `environment file` containing instructions to run the application.

Detailed documentation for creating environment files is located under [docs/environment_file.md](https://github.com/sirca/bdkd_cluster/blob/master/docs/environment_file.md).

### IPython Parallel
As an example, Clusterous comes with an IPython Parallel environment. The `launch` command is used to launch an environment on a running cluster. Once the cluster is launched, you can run IPython Parallel using the `ipython.yml` file located under `subprojects/environments/ipython-lite` in the Clusterous source. To launch, type the following (assuming you are in the bdkd_cluster root folder):

    clusterous launch subprojects/environments/ipython-lite/ipython.yml
    
You will get detailed output as Clusterous launched IPython Parallel. When you run it for the first time (to be technical, for the first time with your configured S3 bucket), it takes some time to launch as it builds an IPython Parallel Docker image. This built image is stored in the S3 bucket you specified in the configuration file.

Once it has launched, Clusterous will output a URL to the IPython notebook on your cluster. Open this URL in your web browser to access the IPython notebook.

## Terminating the cluster
Once you are done, run the `terminate` subcommand to stop the cluster.

    clusterous terminate


## Getting the Clusterous source
```
git clone https://<username>@github.com/sirca/bdkd_cluster.git
cd bdkd_cluster
```

### Contributing
If making changes to the source, it is best to use virtualenv. In your virtual environment, run `setup.py` in `develop` mode.
    
    python setup.py develop


## Other commands
### Set working cluster
Useful when switching between multiple clusters
```
clusterous workon testcluster
```

### List files on shared volume
```
clusterous ls
```

### Upload files
```
clusterous put tests
clusterous ls
```

### Download files
```
clusterous get tests /tmp
ls -al /tmp/tests
```

### Remove files on shared volume
```
clusterous rm tests
clusterous ls
```

### Build docker image
```
cd subprojects/environments/basic-python
clusterous build-image image bdkd:sample_v1
```

### Get information about a Docker image
```
clusterous image-info bdkd:sample_v1
```

### Destroy environment
```
clusterous destroy
clusterous status
```


