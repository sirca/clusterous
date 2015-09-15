import cluster
import logging

class ClusterBuilder(object):
    """
    Builds a cluster
    """
    def __init__(self, cluster, cluster_name, cluster_args, logging_system_level=0, 
                 shared_volume_size=None, controller_instance_type=None):
        self._logging_system_level = logging_system_level
        self._shared_volume_size = shared_volume_size
        self._controller_instance_type = controller_instance_type
        self._cluster_args = cluster_args
        self._cluster_name = cluster_name
        self._cluster = cluster
        self._started = False

        self._logger = logging.getLogger(__name__)


    def start_cluster(self):
        if self._started:
            return False

        self._logger.debug('Cluster params={0}'.format(self._cluster_args))
        nodes_info = []
        for name, params in self._cluster_args.iteritems():
            nodes_info.append((params['count'], params['type'], name))

        try:
            self._cluster.init_cluster(self._cluster_name, nodes_info, self._logging_system_level,
                                       self._shared_volume_size, self._controller_instance_type)
            self._started = True
        except cluster.ClusterException as e:
            self._logger.error(e)
            self._started = False

        return self._started
