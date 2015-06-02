import clusterous.defaults

class Clusterous(object):
    """
    Clusterous application
    """
    def __init__(self):
        self.clusters = []
        self._read_config()

    def _read_config(self):
        """
        Read and validate global configuration
        """
        print "reading config: ", defaults.DEFAULT_CONFIG_FILE

    def start_cluster(self, args):
        """
        Create a new cluster from profile file
        """
        pass


    def list_clusters(self, args):
        pass

    def get_cluster(self, cluser_name):
        """
        Get a Cluster object by name
        """
        pass
