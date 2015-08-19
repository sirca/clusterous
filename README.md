# CLUSTEROUS
Cluster compute tool

### Clone repo
```
git clone https://<username>@github.com/sirca/bdkd_cluster.git
cd bdkd_cluster
python setup.py install
```

### Setup AWS keys
```
vi ~/.clusterous.yml
```

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

### Setup cluster profile
```
vi testcluster.yml
```

```yaml
- Default:
    cluster_name: testcluster
    num_instances: 1
    instance_type: t2.micro
```

### Start cluster
```
clusterous --verbose start testcluster.yml
```

### Cluster status
```
clusterous status
```

### Set working cluster
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

### Get information of docker image
```
clusterous image-info bdkd:sample_v1
```

### Launch environment
```
cd subprojects/environments/basic-python
clusterous launch basic-python-env.yml
clusterous status
```

### Destroy environment
```
clusterous destroy
clusterous status
```

### Terminate cluster
```
clusterous --verbose terminate testcluster
clusterous status
```
