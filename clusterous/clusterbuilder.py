import cluster

class ClusterBuilder(object):
    """
    Base class for all cluster builders
    """
    pass

class DefaultClusterBuilder(ClusterBuilder):
    """
    Builds a standard cluster
    """
    def __init__(self, profile, cluster):
        self._profile_name = profile.keys()[0] 
        self._profile = profile[self._profile_name]

        self._cluster = cluster
        self._launched = False
        

    def start_cluster(self):
        if self._launched:
            return False
        
        self._cluster.init_cluster(self._profile['cluster_name'])
        




