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
