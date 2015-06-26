# Custom Ansible Modules
Example of IPython Parallel been deployed on the cluster via ansible scripts

## Steps:
### 1 Build docker image
clusterous build-image testcluster /Users/lolo/virtualenvs/bdkd/clusterous/subprojects/ansible/custom_module/data/docker/ipython bdkd:ipython

### 2 Check docker image
  clusterous image-info testcluster bdkd:ipython

### 3 Find controller's ip and Copy data
cat ~/.clusterous/current_controller
scp -r -i ~/.ssh/bdkd-sirca.pem /Users/lolo/virtualenvs/bdkd/clusterous/subprojects/ansible/custom_module/data/* root@54.79.76.90:/home/data/

### 4 Deploy ipython parallel on cluster
ansible-playbook -i ~/.clusterous/current_controller --private-key ~/.ssh/bdkd-sirca.pem 01_ipython_deploy.yml
ansible-playbook -i ~/.clusterous/current_controller --private-key ~/.ssh/bdkd-sirca.pem 02_ipython_scale.yml
ansible-playbook -i ~/.clusterous/current_controller --private-key ~/.ssh/bdkd-sirca.pem 03_ipython_destroy.yml
