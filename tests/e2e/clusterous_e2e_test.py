import sys
import boto
import os
import yaml
from StringIO import StringIO

from mock import MagicMock
import pytest

from clusterous.cli import main
from clusterous import defaults

CLUSTEROUS_CONFIG_FILE = '~/.clusterous.yml'
E2E_CLUSTER_NAME = 'e2etestcluster'
E2E_PROFILE_FILE = 'data/test-cluster.yml'
E2E_ENVIRONMENT_FILE = 'data/cluster-envs/basic-python-env.yml'

class TestClusterousE2ETest:
    def _cli_run(self, cmd):
        stdout, stderr = StringIO(), StringIO()
        sys.stdout, sys.stderr = stdout, stderr
        rc = main(cmd.split())
        return rc, stdout.getvalue(), stderr.getvalue()

    def _cluster_destroy(self):
        rc, stdout, stderr = self._cli_run('destroy --confirm')
        return rc == 0 and self._no_cluster_running()

    def _no_cluster_running(self):
        rc, stdout, stderr = self._cli_run('status')
        return rc == 0 and 'No working cluster has been set' in stderr

    def _cluster_running(self):
        rc, stdout, stderr = self._cli_run('status')
        return rc == 0 and E2E_CLUSTER_NAME in stdout and 'running' in stdout

    def _cluster_wrong_state(self):
        rc, stdout, stderr = self._cli_run('status')
        return rc == 0 and 'destroy' in stderr

    def _get_aws_connection(self):
        with open(os.path.expanduser(CLUSTEROUS_CONFIG_FILE), 'r') as stream:
            contents = yaml.load(stream)
        c = contents[0]['AWS']
        conn = boto.ec2.connect_to_region(c['region'], aws_access_key_id=c['access_key_id'],aws_secret_access_key=c['secret_access_key'])
        return conn

    def test_cluster_create(self):
        # Destroy if cluster present
        if self._cluster_running() or self._cluster_wrong_state():
            self._cluster_destroy()
    
        # Create cluster
        rc, stdout, stderr = self._cli_run('create {0}'.format(E2E_PROFILE_FILE))
        assert rc == 0
        assert 'Cluster "{0}" created'.format(E2E_CLUSTER_NAME) in stderr
        assert self._cluster_running() == True
        
    def test_cluster_status_on_running_cluster_with_default_profile(self):
        assert self._cluster_running(), 'Cluster not running'
        rc, stdout, stderr = self._cli_run('status')
        assert rc == 0
        assert E2E_CLUSTER_NAME in stdout and 'instances running' in stdout and 'Uptime' in stdout
        assert 'Node Name' in stdout and '[controller]' in stdout and '[nat]' in stdout
        assert 'Shared Volume' in stdout and 'used of 20G' in stdout
    
    def test_cluster_run_on_running_cluster_with_default_profile(self):
        # Check if cluster is running
        assert self._cluster_running(), 'Cluster not running'
         
        # Run environment
        rc, stdout, stderr = self._cli_run('run {0}'.format(E2E_ENVIRONMENT_FILE))
        assert rc == 0, 'Fail to run environment'
        assert (('Launched' in stderr and 'components' in stderr) or ('Environment already' in stderr ))
 
    def test_cluster_quit_on_running_cluster_with_default_profile(self):
        # Check if cluster is running
        assert self._cluster_running(), 'Cluster not running'

        # Quit environment
        rc, stdout, stderr = self._cli_run('quit --confirm')
        assert rc == 0
        assert 'applications successfully destroyed' in stderr or 'No application to destroy' in stderr

    def test_cluster_add_nodes_on_running_cluster_with_default_profile(self):
        # Check if cluster is running
        assert self._cluster_running(), 'Cluster not running'
           
        # Get AWS connection
        conn = self._get_aws_connection()
        assert conn, 'Failed connecting to AWS. Check AWS keys'
   
        # Get number of instances running before adding node
        instance_filters = { 'tag:{0}'.format(defaults.instance_tag_key):  [E2E_CLUSTER_NAME,], 'instance-state-name': ['running', 'pending']}
        num_instances_before = len(conn.get_only_instances(filters=instance_filters))
           
        # Adding node
        rc, stdout, stderr = self._cli_run('add-nodes 1')
        assert rc, 'Failed to add 1 node'
        assert '1 nodes of type "worker" added' in stderr
        num_instances_after = len(conn.get_only_instances(filters=instance_filters))
           
        # Checking node added
        assert (num_instances_before + 1) == num_instances_after
  
    def test_cluster_rm_nodes_on_running_cluster_with_default_profile(self):
        # Check if cluster is running
        assert self._cluster_running(), 'Cluster not running'
           
        # Get AWS connection
        conn = self._get_aws_connection()
        assert conn, 'Failed connecting to AWS. Check AWS keys'
   
        # Get number of instances running before adding node
        instance_filters = { 'tag:{0}'.format(defaults.instance_tag_key):  [E2E_CLUSTER_NAME,], 'instance-state-name': ['running', 'pending']}
        num_instances_before = len(conn.get_only_instances(filters=instance_filters))
  
        # Removing node
        rc, stdout, stderr = self._cli_run('rm-nodes 1')
        assert rc, 'Failed to remove node'
        assert '1 nodes of type "worker" removed' in stderr
        num_instances_after = len(conn.get_only_instances(filters=instance_filters))
  
        # Checking node removed
        assert (num_instances_before - 1) == num_instances_after
         
    def test_cluster_destroy(self):
        # Check if cluster is running or in wrong state
        assert self._cluster_running() or self._cluster_wrong_state(), 'There is no cluster to destroy'
          
        # Destroying cluster
        rc, stdout, stderr = self._cli_run('destroy --confirm')
        assert rc == 0, 'Fail to destroy cluster'
        assert self._no_cluster_running()
