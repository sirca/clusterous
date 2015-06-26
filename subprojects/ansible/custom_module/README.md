# Custom Ansible Modules
Example of IPython Parallel been deployed on the cluster via ansible scripts

## Steps:
### Build docker image
clusterous build-image testcluster /Users/lolo/virtualenvs/bdkd/clusterous/subprojects/ansible/custom_module/data/docker/ipython bdkd:ipython

### Check docker image
  clusterous image-info testcluster bdkd:ipython

### Copy data
### Find controllers ip
cat ~/.clusterous/current_controller
workon bdkd
cd clusterous/subprojects/ansible/custom_module
scp -r -i ~/.ssh/bdkd-sirca.pem data/* root@54.79.76.90:/home/data/

### Deploy ipython parallel on cluster
ansible-playbook -i ~/.clusterous/current_controller --private-key ~/.ssh/bdkd-sirca.pem 01_ipython_deploy.yml
ansible-playbook -i ~/.clusterous/current_controller --private-key ~/.ssh/bdkd-sirca.pem 02_ipython_scale.yml
ansible-playbook -i ~/.clusterous/current_controller --private-key ~/.ssh/bdkd-sirca.pem 03_ipython_destroy.yml
