# Copyright 2015 Nicta
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import sys
import boto
import os
import yaml
from StringIO import StringIO
import urllib2

from mock import MagicMock
import pytest

from clusterous.cli import main
from clusterous import defaults
from sshtunnel import SSHTunnelForwarder

import marathon

CLUSTEROUS_CONFIG_FILE = '~/.clusterous.yml'
E2E_CLUSTER_NAME = 'e2etestcluster'
E2E_CLUSTER_FILE = 'data/test-cluster.yml'
E2E_ENVIRONMENT_FILE = 'data/cluster-envs/basic-python-env.yml'

MSG_NOT_WORKING_CLUSTER = 'No working cluster has been set'

with open(os.path.expanduser(CLUSTEROUS_CONFIG_FILE), 'r') as stream:
    CLUSTEROUS_CONFIG = yaml.load(stream)
    AWS_CONFIG = CLUSTEROUS_CONFIG.get('profiles',{}).get(CLUSTEROUS_CONFIG.get('current_profile',{})).get('config',{})

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
        return rc == 0 and MSG_NOT_WORKING_CLUSTER in stderr

    def _cluster_running(self):
        rc, stdout, stderr = self._cli_run('status')
        return rc == 0 and E2E_CLUSTER_NAME in stdout and 'running' in stdout

    def _cluster_wrong_state(self):
        rc, stdout, stderr = self._cli_run('status')
        return rc == 0 and 'destroy' in stderr

    def _get_aws_connection(self):
        conn = boto.ec2.connect_to_region(AWS_CONFIG['region'], aws_access_key_id=AWS_CONFIG['access_key_id'],aws_secret_access_key=AWS_CONFIG['secret_access_key'])
        return conn

    def _get_cluster_info(self):
        cluster_info_file = os.path.expanduser(defaults.cluster_info_file)
        if not os.path.isfile(cluster_info_file):
            return {}
        f = open(os.path.expanduser(cluster_info_file), 'r')
        cluster_info = yaml.load(f)
        return cluster_info

    def test_cluster_create(self):
        # Destroy if cluster present
        if self._cluster_running() or self._cluster_wrong_state():
            self._cluster_destroy()
    
        # Create cluster
        rc, stdout, stderr = self._cli_run('create {0}'.format(E2E_CLUSTER_FILE))
        assert rc == 0
        assert 'Cluster "{0}" created'.format(E2E_CLUSTER_NAME) in stderr
        assert self._cluster_running() == True

        # Check tunnel
        f = urllib2.urlopen('http://localhost:8888/')
        assert f.getcode() == 200
        
    def test_cannot_create_cluster_on_running_cluster(self):
        # Check if cluster is running
        assert self._cluster_running(), 'Cluster not running'
    
        # Create cluster
        rc, stdout, stderr = self._cli_run('create {0}'.format(E2E_CLUSTER_FILE))
        assert rc == 1
        assert 'A cluster by the name "{0}" is already running, cannot start'.format(E2E_CLUSTER_NAME) in stderr
  
    def test_cluster_instances_on_running_cluster(self):
        # Check if cluster is running
        assert self._cluster_running(), 'Cluster not running'
           
        # Check number of nodes and types
        rc, stdout, stderr = self._cli_run('status')
        assert rc == 0
        rc_trim = stdout.replace('\n','').replace(' ','')
        assert 'mastert2.micro1' in rc_trim
        assert 'workert2.micro1' in rc_trim
            
    def test_cluster_status_on_running_cluster(self):
        assert self._cluster_running(), 'Cluster not running'
        rc, stdout, stderr = self._cli_run('status')
        assert rc == 0
        assert E2E_CLUSTER_NAME in stdout and 'instances running' in stdout and 'Uptime' in stdout
        assert 'Node Name' in stdout and '[controller]' in stdout and '[nat]' in stdout
        assert 'Shared Volume' in stdout and 'used of 20G' in stdout
    
    def test_number_of_running_components_on_running_cluster(self):
        # Check if cluster is running
        assert self._cluster_running(), 'Cluster not running'
   
        # Check number of running components
        components = {}
        with SSHTunnelForwarder((self._get_cluster_info().get('nat_ip'),
                                 defaults.nat_ssh_port_forwarding), 
                                ssh_username=defaults.cluster_username, 
                                ssh_private_key=os.path.expanduser(AWS_CONFIG['key_file']), 
                                remote_bind_address=('127.0.0.1', defaults.marathon_port)) as tunnel:
            marathon_url = 'http://localhost:{0}'.format(tunnel.local_bind_port)
            client = marathon.MarathonClient(servers=marathon_url, timeout=600)
            for app_name in [ a.id.strip('/') for a in client.list_apps() ]:
                if app_name not in components:
                    components[app_name] = 0
                components[app_name] += client.get_app(app_name).instances
        assert components['master'] == 1
        assert components['engine'] == 2
   
    def test_cluster_quit_on_running_cluster(self):
        # Check if cluster is running
        assert self._cluster_running(), 'Cluster not running'

        # Quit environment
        rc, stdout, stderr = self._cli_run('quit --confirm')
        assert rc == 0
        assert 'applications successfully destroyed' in stderr or 'No application to destroy' in stderr

    def test_cluster_run_env_on_running_cluster(self):
        # Check if cluster is running
        assert self._cluster_running(), 'Cluster not running'

        # Run environment
        rc, stdout, stderr = self._cli_run('run {0}'.format(E2E_ENVIRONMENT_FILE))
        assert rc == 0, 'Fail to run environment'
        assert (('Launched' in stderr and 'components' in stderr) or ('Environment already' in stderr ))

        # Checking tunnel
        f = urllib2.urlopen('http://localhost:8888/')
        assert f.getcode() == 200

        # Quit again
        rc, stdout, stderr = self._cli_run('quit --confirm')

    def test_cluster_add_nodes_on_running_cluster(self):
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
  
    def test_cluster_rm_nodes_on_running_cluster(self):
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
    
    def test_execute_commands_on_destroyed_cluster(self):
        # Check if not running cluster
        assert self._no_cluster_running(), 'Cluster running'
 
        # Check status
        rc, stdout, stderr = self._cli_run('status')
        return rc == 0 and MSG_NOT_WORKING_CLUSTER in stderr
 
        # Check destroy
        rc, stdout, stderr = self._cli_run('destroy --confirm')
        return rc == 0 and MSG_NOT_WORKING_CLUSTER in stderr
 
        # Check run
        rc, stdout, stderr = self._cli_run('run {0}'.format(E2E_ENVIRONMENT_FILE))
        return rc == 0 and MSG_NOT_WORKING_CLUSTER in stderr
 
        # Check quit
        rc, stdout, stderr = self._cli_run('quit --confirm')
        return rc == 0 and MSG_NOT_WORKING_CLUSTER in stderr
 
        # Check add-nodes
        rc, stdout, stderr = self._cli_run('add-nodes 1')
        return rc == 0 and MSG_NOT_WORKING_CLUSTER in stderr
 
        # Check remove-nodes
        rc, stdout, stderr = self._cli_run('rm-nodes 1')
        return rc == 0 and MSG_NOT_WORKING_CLUSTER in stderr
 
        # Check connect
        rc, stdout, stderr = self._cli_run('connect notebook')
        return rc == 0 and MSG_NOT_WORKING_CLUSTER in stderr
 
        # Check ls
        rc, stdout, stderr = self._cli_run('ls')
        return rc == 0 and MSG_NOT_WORKING_CLUSTER in stderr

    def test_invalid_params_file_on_destroyed_cluster(self):
        # Check if not running cluster
        assert self._no_cluster_running(), 'Cluster running'

        # Create cluster
        rc, stdout, stderr = self._cli_run('create data/test-cluster-bad.yml')
        assert rc == 1
        return rc == 1 and 'Error in cluster parameters file' in stderr
