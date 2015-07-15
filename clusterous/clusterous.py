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

    class Verbosity:
        DEBUG = 'DEBUG'
        NORMAL = 'INFO'
        QUIET = 'WARNING'

    def __init__(self, config_file=defaults.DEFAULT_CONFIG_FILE, log_level=Verbosity.NORMAL):
        self.clusters = []
        self._config = {}

        self._configure_logger(log_level)
        self._logger = logging.getLogger()

        try:
            self._read_config(config_file)
        except Exception as e:
            self._logger.error(e)
            sys.exit(e)

        logging.getLogger('boto').setLevel(logging.CRITICAL)

        conf_dir = os.path.expanduser(defaults.local_config_dir)
        if not os.path.exists(conf_dir):
            os.makedirs(conf_dir)

    def _configure_logger(self, level):
        logging_dict = {
                            'version': 1,
                            'disable_existing_loggers': False,
                            'formatters': {
                                'standard': {
                                    'format': '%(message)s'
                                },
                            },
                            'handlers': {
                                'default': {
                                    'level': level,
                                    'class':'logging.StreamHandler',
                                },
                            },
                            'loggers': {
                                '': {
                                    'handlers': ['default'],
                                    'level': level,
                                    'propagate': True
                                },
                            }
                        }
        logging.config.dictConfig(logging_dict)

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
            env = environment.Environment(env_file.spec, env_file.base_path, cl)
            env.launch_from_spec()
        except environment.EnvironmentError as e:
            self._logger.error(e)
            self._logger.error('Failed to launch environment')
            return False
        return True

    def list_clusters(self, args):
        pass

    def get_cluster(self, cluser_name):
        """
        Get a Cluster object by name
        """
        pass
