
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
