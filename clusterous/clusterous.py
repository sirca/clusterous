import yaml
import os
import sys

import defaults
from cluster import Cluster
import clusterbuilder

class ParseError(Exception):
    pass

class Clusterous(object):
    """
    Clusterous application
    """
    def __init__(self):
        self.clusters = []
        self._config = {}
        try:
            self._read_config()
        except Exception as e:
            sys.exit(e)        

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

        # TODO: determine application name from profile file, and send to 
        # appropriate Cluster Builder if necessary

        # Init Cluster object
        cl = Cluster(self._config)

        # Create Cluster Builder, passing in profile and Cluster
        builder = clusterbuilder.DefaultClusterBuilder(profile_contents, cl)
        builder.start_cluster()



    def list_clusters(self, args):
        pass

    def get_cluster(self, cluser_name):
        """
        Get a Cluster object by name
        """
        pass
