# Custom Ansible Modules
Example of IPython Parallel been deployed on the cluster via ansible scripts.
It assumes you have a cluster running (instructions on root repository).

### IPython example
```
cd subprojects/ansible/custom_module
```

### Check docker image
```
clusterous image-info democluster bdkd:ipython
```

### Build docker image
```
clusterous build-image democluster ./data/docker/ipython bdkd:ipython
```

### Copy data
```
ansible-playbook -i ~/.clusterous/current_controller \
  --private-key ~/.ssh/bdkd-sirca.pem \
  00_sync_folder.yml \
  --extra-vars "src_path=./data dst_path=/home/"
```

### Deploy ipython parallel on cluster
```
ansible-playbook -vvvv -i ~/.clusterous/current_controller --private-key ~/.ssh/bdkd-sirca.pem 00_list_apps.yml
ansible-playbook -i ~/.clusterous/current_controller --private-key ~/.ssh/bdkd-sirca.pem 01_ipython_deploy.yml
ansible-playbook -i ~/.clusterous/current_controller --private-key ~/.ssh/bdkd-sirca.pem 02_ipython_scale.yml
ansible-playbook -i ~/.clusterous/current_controller --private-key ~/.ssh/bdkd-sirca.pem 03_ipython_destroy.yml
```

### Optional: 
#### Mesos:
```
export CONTROLLER_IP=`cat ~/.clusterous/current_controller`
ssh -i ~/.ssh/bdkd-sirca.pem root@$CONTROLLER_IP -L 5050:127.0.0.1:5050 # mesos
Browse: http://localhost:5050
```

#### Marathon:
```
export CONTROLLER_IP=`cat ~/.clusterous/current_controller`
ssh -i ~/.ssh/bdkd-sirca.pem root@$CONTROLLER_IP -L 8080:127.0.0.1:8080 # marathon
Browse: http://localhost:8080
```

#### IPython Notebook:
```
ssh -i ~/.ssh/bdkd-sirca.pem root@54.79.124.206 -L 31080:127.0.0.1:31080 # IPython Notebook
Browse: http://localhost:31080
```
