from mock import patch

from clusterous.clusterous import *
import clusterous.cluster

class TestClusterous:

    @patch.object(Clusterous, '_read_config')
    def test_init(self, _read_config):
        c = Clusterous()
        _read_config.assert_called_once()

    @patch.object(cluster.AWSCluster, 'terminate_cluster')
    def test_terminate_cluster(self, terminate_cluster):
        c = Clusterous()
        c._config = {'AWS': {'dummy': 'val'}}
        cluster_name = 'dummycluster'
        c.terminate_cluster(cluster_name)
        terminate_cluster.assert_called_once_with(cluster_name)
