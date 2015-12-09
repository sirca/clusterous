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

from mock import patch
import pytest

from clusterous.cluster import *

class TestCluster:

    @pytest.fixture()
    def config(self):
        return  {
                    'region': 'dummy',
                    'access_key_id': 'dummy',
                    'secret_access_key': 'dummy',
                    'key_file': 'dummy',
                }

    @patch.object(AWSCluster, '_ec2_vars_dict')
    @patch.object(AWSCluster, '_make_vars_file')
    @patch.object(AWSCluster, '_ansible_env_credentials')
    @patch.object(AnsibleHelper, 'run_playbook')
    @patch.object(AWSCluster, '_create_controller_tunnel')
    def test_init_cluster(self, _create_controller_tunnel, run_playbook, _ansible_env_credentials, _make_vars_file, _ec2_vars_dict, config):
        cl = AWSCluster(config)
        cl.init_cluster('dog')
        assert _ansible_env_credentials.called == True
        assert _make_vars_file.called == True
        assert _ec2_vars_dict.called == True
        assert run_playbook.called == True
        assert _create_controller_tunnel.called == True

    @patch.object(boto.ec2, 'connect_to_region')
    @patch('clusterous.cluster.retry_till_true')
    def test_terminate_cluster(self, retry_till_true, connect_to_region, config):
        cl = AWSCluster(config)
        cl.terminate_cluster('dummy')
        assert connect_to_region.called == True
        assert retry_till_true.called == True

    @patch.object(AWSCluster, '_ec2_vars_dict')
    @patch.object(AWSCluster, '_make_vars_file')
    @patch.object(AWSCluster, '_ansible_env_credentials')
    @patch.object(AnsibleHelper, 'run_playbook')
    @patch.object(AWSCluster, 'docker_build_image')
    def test_docker_build_image(self, docker_build_image, run_playbook, _ansible_env_credentials, _make_vars_file, _ec2_vars_dict, config):
        cl = AWSCluster(config)
        cl.init_cluster('dog')
        assert _ansible_env_credentials.called == True
        assert _make_vars_file.called == True
        assert _ec2_vars_dict.called == True
        assert run_playbook.called == True

    @patch.object(AWSCluster, '_ec2_vars_dict')
    @patch.object(AWSCluster, '_make_vars_file')
    @patch.object(AWSCluster, '_ansible_env_credentials')
    @patch.object(AnsibleHelper, 'run_playbook')
    @patch.object(AWSCluster, 'docker_image_info')
    def test_docker_image_info(self, docker_image_info, run_playbook, _ansible_env_credentials, _make_vars_file, _ec2_vars_dict, config):
        cl = AWSCluster(config)
        cl.init_cluster('dog')
        assert _ansible_env_credentials.called == True
        assert _make_vars_file.called == True
        assert _ec2_vars_dict.called == True
        assert run_playbook.called == True
