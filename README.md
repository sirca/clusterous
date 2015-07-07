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
    clustserous_s3_bucket: xxx
```

### Setup cluster profile
```
vi democluster.yml
```

```yaml
- Default:
    cluster_name: democluster
    num_instances: 1
    instance_type: t2.micro
```

### Start cluster
```
clusterous --verbose start democluster.yml
```

### Terminate cluster
```
clusterous --verbose terminate democluster
```
