import cluster
import logging
import tempfile
import yaml

class ClusterBuilder(object):
    """
    Builds a cluster
    """
    def __init__(self, cluster):

        self._cluster = cluster
        self._started = False

        self._logger = logging.getLogger(__name__)


    def start_cluster(self, cluster_name, cluster_spec, logging_system_level=0,
                        shared_volume_size=None, controller_instance_type=None, shared_volume_id=None):
        if self._started:
            return False

        self._logger.debug('Cluster params={0}'.format(cluster_spec))
        nodes_info = []
        for name, params in cluster_spec.iteritems():
            nodes_info.append((params['count'], params['type'], name))

        try:
            self._cluster.init_cluster(cluster_name, cluster_spec, nodes_info, logging_system_level,
                                        shared_volume_size, controller_instance_type, shared_volume_id)
            self._started = True
        except cluster.ClusterException as e:
            self._logger.error(e)
            self._started = False


        return self._started


    def _validate_node_name(self, spec, node_name):
        actual_node_name = node_name
        is_valid = True

        scalable_node_types = []
        for name, params in spec.iteritems():
            if params.get('scalable', False):
                scalable_node_types.append(name)

        if len(scalable_node_types) > 1:
            node_types_str = ', '.join(scalable_node_types)
            if node_name == None:
                self._logger.debug('Scalable node types: {0}'.format(scalable_node_types))
                self._logger.error('Must specify node types as one of: {0}'.format(node_types_str))
                is_valid = False
            elif node_name not in scalable_node_types:
                self._logger.error('Node type must be one of: {0}'.format(node_types_str))
                is_valid = False
        elif len(scalable_node_types) == 1:
            if node_name and node_name != scalable_node_types[0]:
                self._logger.error('"{0}" is not a known node type'.format(node_name))
                is_valid = False
            elif node_name == None:
                actual_node_name = scalable_node_types[0]
        elif len(scalable_node_types) == 0:
            self._logger.error('No node types available to be scaled')
            is_valid = False

        return is_valid, actual_node_name


    def add_nodes(self, num_nodes, node_name=None):
        spec = self._cluster.get_cluster_spec()
        is_valid, actual_node_name = self._validate_node_name(spec, node_name)

        if not is_valid:
            return False, 'Error adding nodes', None

        try:
            instance_type = spec[actual_node_name]['type']
        except KeyError as e:
            raise ValueError('Cannot find instance type for "{0}" in cluster spec'.format(actual_node_name))

        success = self._cluster.add_nodes(num_nodes, instance_type, actual_node_name)

        if success:
            self._logger.info('{0} nodes of type "{1}" added'.format(num_nodes, actual_node_name))
            return True, '', actual_node_name
        else:
            return False, 'Error adding nodes', None


    def rm_nodes(self, num_nodes, node_name=None):
        spec = self._cluster.get_cluster_spec()
        message = ''

        is_valid, actual_node_name = self._validate_node_name(spec, node_name)
        if not is_valid:
            return False, 'Error removing nodes', None
        try:
            instance_type = spec[actual_node_name]['type']
        except KeyError as e:
            raise ValueError('Cannot find instance type for "{0}" in cluster spec'.format(actual_node_name))

        num_removed = self._cluster.rm_nodes(num_nodes, actual_node_name)

        if num_removed < 0:
            message = 'An error occured when removing nodes'
        else:
            self._logger.info('{0} nodes of type "{1}" removed'.format(num_removed, actual_node_name))

        return (num_removed >= 0), message, actual_node_name
