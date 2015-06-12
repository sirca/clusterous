from mock import patch

from clusterous.cluster import *
from clusterous.clusterbuilder import *


class TestClusterBuilder:

    def _dummy_profile(self):
        profile_vals = {
                    'cluster_name': 'abcd',
                    'num_instances': 4,
                    'instance_type': 't2.micro'
        }
        return  { 'test': profile_vals }

    @patch.object(Cluster, 'init_cluster')
    @patch.object(Cluster, 'launch_nodes')
    def test_start_cluster(self, launch_nodes, init_cluster):
        cluster = Cluster({'dummy': 'value'})

        cb = DefaultClusterBuilder(self._dummy_profile(), cluster)
        cb.start_cluster()
        
        init_cluster.assert_called_once_with('abcd')
        launch_nodes.assert_called_once()


