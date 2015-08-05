import yaml
import os
import sys
import logging
import logging.config
import boto

import defaults
import cluster
import clusterbuilder
import environmentfile
import environment
from helpers import AnsibleHelper


class ParseError(Exception):
    pass

class Clusterous(object):
    """
    Clusterous application
    """

    def __init__(self, config_file=defaults.DEFAULT_CONFIG_FILE):
        self.clusters = []
        self._config = {}

        self._logger = logging.getLogger(__name__)

        try:
            self._read_config(config_file)
        except Exception as e:
            self._logger.error(e)
            sys.exit(e)

        conf_dir = os.path.expanduser(defaults.local_config_dir)
        if not os.path.exists(conf_dir):
            os.makedirs(conf_dir)

    def _read_config(self, config_file):
        """
        Read and validate global configuration
        """

        stream = open(os.path.expanduser(config_file), 'r')
        contents = yaml.load(stream)
        stream.close()

        # Validate
        if len(contents) < 1:
            raise ParseError('Could not find configuration information in {0}'
                             .format(defaults.DEFAULT_CONFIG_FILE))

        # TODO: validate properly by sending to provisioner
        self._config = contents[0]

    def make_cluster_object(self, cluster_name=None, cluster_name_required=True):
        cl = None
        if 'AWS' in self._config:
            cl = cluster.AWSCluster(self._config['AWS'], cluster_name, cluster_name_required)
        else:
            self._logger.error('Unknown cloud type')
            raise ValueError('Unknown cloud type')

        return cl

    def start_cluster(self, args):
        """
        Create a new cluster from profile file
        """
        stream = open(os.path.expanduser(args.profile_file), 'r')
        profile_contents = yaml.load(stream)[0]
        stream.close()

        # Init Cluster object
        cl = self.make_cluster_object(cluster_name_required=False)

        # Create Cluster Builder, passing in profile and Cluster
        builder = clusterbuilder.DefaultClusterBuilder(profile_contents, cl)
        self._logger.info('Starting cluster')
        builder.start_cluster()
        self._logger.info('Started cluster')

    def docker_build_image(self, args):
        """
        Create a new docker image
        """
        full_path = os.path.abspath(args.dockerfile_folder)

        if not os.path.isdir(full_path):
            self._logger.error("Error: Folder '{0}' does not exists.".format(full_path))
            return False

        if not os.path.exists("{0}/Dockerfile".format(full_path)):
            self._logger.error("Error: Folder '{0}' does not have a Dockerfile.".format(full_path))
            return False

        cl = self.make_cluster_object()
        cl.docker_build_image(full_path, args.image_name)

    def docker_image_info(self, image_name):
        """
        Gets information of a Docker image
        """
        cl = self.make_cluster_object()
        return cl.docker_image_info(image_name)

    def sync_put(self, local_path, remote_path):
        """
        Sync local folder to the cluster
        """
        cl = self.make_cluster_object()
        return cl.sync_put(local_path, remote_path)

    def sync_get(self, local_path, remote_path):
        """
        Sync folder from the cluster to local
        """
        cl = self.make_cluster_object()
        return cl.sync_get(local_path, remote_path)

    def ls(self, remote_path):
        """
        List content of a folder on the on cluster
        """
        cl = self.make_cluster_object()
        return cl.ls(remote_path)

    def rm(self, remote_path):
        """
        Delete content of a folder on the on cluster
        """
        cl = self.make_cluster_object()
        return cl.rm(remote_path)

    def cluster_connect(self, component_name):
        # Check if component_name exists
        cl = self.make_cluster_object()
        env = environment.Environment(cl)
        runnin_apps = env.get_running_component_info()
        app = runnin_apps.get(component_name)
        if app is None:
            message = "Component '{0}' does not exist".format(component_name)
            return (False, message)

        if app > 1:
            message = "Cannot connect to '{0}' because there is more than one instance running on the cluster".format(component_name)
            return (False, message)

        return cl.cluster_connect(component_name)

    def cluster_status(self):
        cl = self.make_cluster_object()
        env = environment.Environment(cl)
        all_info = {'cluster': cl.info_status(),
                    'instances': cl.info_instances(),
                    'applications': env.get_running_component_info(),
                    'volume': cl.info_shared_volume()
                    }
        return (True, all_info)

    def workon(self, cluster_name):
        """
        Sets a working cluster
        """
        cl = self.make_cluster_object(cluster_name)
        return cl.workon()

    def terminate_cluster(self):
        cl = self.make_cluster_object()
        self._logger.info('Terminating cluster {0}'.format(cl.cluster_name))
        cl.terminate_cluster()

    def launch_environment(self, environment_file):
        cl = self.make_cluster_object()

        try:
            env_file = environmentfile.EnvironmentFile(environment_file)
            env = environment.Environment(cl)
            success, message = env.launch_from_spec(env_file)
        except environment.Environment.LaunchError as e:
            self._logger.error(e)
            self._logger.error('Failed to launch environment')
            return False, ''

        return success, message

    def destroy_environment(self, tunnel_only=False):
        cl = self.make_cluster_object()

        success = True
        if not tunnel_only:
            # Destroy running apps
            env = environment.Environment(cl)
            success &= env.destroy()
        else:
            self._logger.info('Only removing any local SSH tunnels')

        success &= cl.delete_all_permanent_tunnels()
        return success

    def list_clusters(self, args):
        pass

    def get_cluster(self, cluser_name):
        """
        Get a Cluster object by name
        """
        pass
