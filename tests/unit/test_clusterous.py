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

    @patch.object(cluster.AWSCluster, 'docker_build_image')
    def test_terminate_cluster(self, docker_build_image):
        c = Clusterous()
        c._config = {'AWS': {'dummy': 'val'}}
        cluster_name = 'dummycluster'
        c.docker_build_image(cluster_name)
        docker_build_image.assert_called_once_with(cluster_name)

    @patch.object(cluster.AWSCluster, 'docker_image_info')
    def test_terminate_cluster(self, docker_image_info):
        c = Clusterous()
        c._config = {'AWS': {'dummy': 'val'}}
        cluster_name = 'dummycluster'
        c.docker_image_info(cluster_name)
        docker_image_info.assert_called_once_with(cluster_name)
