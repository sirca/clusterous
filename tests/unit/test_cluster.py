from mock import patch

from clusterous.cluster import *

class TestCluster:

    @patch.object(AWSCluster, '_ec2_vars_dict')
    @patch.object(AWSCluster, '_make_vars_file')
    @patch.object(AWSCluster, '_ansible_env_credentials')
    @patch.object(AnsibleHelper, 'run_playbook')
    @patch.object(AWSCluster, '_create_controller_tunnel')
    def test_init_cluster(self, _create_controller_tunnel, run_playbook, _ansible_env_credentials, _make_vars_file, _ec2_vars_dict):
        config = {'key_file': 'dummy'}
        cl = AWSCluster(config)
        cl.init_cluster('dog')
        _ansible_env_credentials.assert_called()
        _make_vars_file.assert_called()
        _ec2_vars_dict.assert_called()
        run_playbook.assert_called()
        _create_controller_tunnel.assert_called()
