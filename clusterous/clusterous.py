import yaml
import os
import sys
import logging

import defaults
import cluster
import clusterbuilder

class ParseError(Exception):
    pass

class Clusterous(object):
    """
    Clusterous application
    """

    class Verbosity:
        DEBUG = logging.DEBUG
        NORMAL = logging.INFO
        QUIET = logging.WARNING

    def __init__(self, log_level=Verbosity.NORMAL):
        self.clusters = []
        self._config = {}

        logging.basicConfig(level=log_level, format='%(message)s')
        self._logger = logging.getLogger()

        try:
            self._read_config()
        except Exception as e:
            self._logger.error(e)
            sys.exit(e)

        conf_dir = os.path.expanduser(defaults.local_config_dir)
        if not os.path.exists(conf_dir):
            os.makedirs(conf_dir)

    def _read_config(self):
        """
        Read and validate global configuration
        """

        stream = open(os.path.expanduser(defaults.DEFAULT_CONFIG_FILE), 'r')
        contents = yaml.load(stream)
        stream.close()

        # Validate
        if len(contents) < 1:
            raise ParseError('Could not find configuration information in {0}'
                             .format(defaults.DEFAULT_CONFIG_FILE))

        # TODO: validate properly by sending to provisioner
        self._config = contents[0]


    def start_cluster(self, args):
        """
        Create a new cluster from profile file
        """
        stream = open(os.path.expanduser(args.profile_file), 'r')
        profile_contents = yaml.load(stream)[0]
        stream.close()


        # Init Cluster object
        if 'AWS' in self._config:
            cl = cluster.AWSCluster(self._config['AWS'])
        else:
            self._logger.error('Unknown cloud type')
            raise ValueError('Unknown cloud type')


        # Create Cluster Builder, passing in profile and Cluster
        builder = clusterbuilder.DefaultClusterBuilder(profile_contents, cl)
        self._logger.info('Starting cluster')
        builder.start_cluster()
        self._logger.info('Started cluster')



    def list_clusters(self, args):
        pass

    def get_cluster(self, cluser_name):
        """
        Get a Cluster object by name
        """
        pass
