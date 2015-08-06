import cluster
import logging

class ClusterBuilder(object):
    """
    Builds a cluster
    """
    def __init__(self, cluster, cluster_name, cluster_args):
        self._cluster_args = cluster_args
        self._cluster_name = cluster_name
        self._cluster = cluster
        self._launched = False

        self._logger = logging.getLogger(__name__)


    def start_cluster(self):
        if self._launched:
            return False

        self._logger.debug('Cluster params={0}'.format(self._cluster_args))
        self._cluster.init_cluster(self._cluster_name)
        for name, params in self._cluster_args.iteritems():
            self._cluster.launch_nodes(params['count'], params['type'], name)
        self._launched = True
