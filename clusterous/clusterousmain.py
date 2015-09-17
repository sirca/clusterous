import yaml
import os
import sys
import logging
import logging.config
import boto

import defaults
import cluster
import clusterbuilder
from environmentfile import EnvironmentFile
import environment
from helpers import AnsibleHelper


class ClusterousError(Exception):
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
            raise ClusterousError('Could not find configuration information in {0}'
                             .format(defaults.DEFAULT_CONFIG_FILE))

        # TODO: validate properly by sending to provisioner
        self._config = contents[0]

    def _read_profile(self, profile_file):
        """
        Given user supplied file path, read in and validate profile file.
        Return dictionary contents
        """
        full_path = os.path.abspath(os.path.expanduser(profile_file))
        if not os.path.isfile(full_path):
            raise ClusterousError('Cannot open file "{0}"'.format(profile_file))
        stream = open(full_path, 'r')
        try:
            contents = yaml.load(stream)
        except yaml.YAMLError as e:
            raise ClusterousError('Error processing YAML file {0}'.format(e))

        # Validate profile file
        validated = {}
        try:
            validated['cluster_name'] = contents['cluster_name']
        except KeyError as e:
            raise ClusterousError('No "cluster_name" field in "{0}"'.format(profile_file))

        validated['central_logging_level'] = contents.get('central_logging_level', 0)
        validated['parameters'] = contents.get('parameters', {})

        environment_file = None
        if 'environment_file' in contents:
            # Get absolute path of environment file
            # The given file path is assumed to be relative to the location of the profile file
            base_path = os.path.dirname(full_path)
            environment_file = os.path.join(base_path, contents['environment_file'])

        validated['environment_file'] = environment_file

        for key in contents.keys():
            if key not in validated.keys():
                raise ClusterousError('Unknown field "{0}" in profile file "{1}"'.format(key, profile_file))

        return validated

    def make_cluster_object(self, cluster_name=None, cluster_name_required=True):
        cl = None
        if 'AWS' in self._config:
            cl = cluster.AWSCluster(self._config['AWS'], cluster_name, cluster_name_required)
        else:
            self._logger.error('Unknown cloud type')
            raise ClusterousError('Unknown cloud type')

        return cl

    def start_cluster(self, profile_file, launch_env=True):
        """
        Create a new cluster from profile file
        """
        profile = self._read_profile(profile_file)
        env_file = None
        cluster_spec = None
        if profile['environment_file']:
            env_file = EnvironmentFile(profile['environment_file'], profile['parameters'])

        # If necessary, obtain cluster spec
        if not env_file or (not env_file.spec['cluster']):
            default_file_path = defaults.get_script(defaults.default_cluster_def_filename)
            cluster_env_file = EnvironmentFile(default_file_path, profile['parameters'])
            cluster_spec = cluster_env_file.spec['cluster']
        else:
            cluster_spec = env_file.spec['cluster']

        self._logger.debug('Actual cluster spec: {0}'.format(cluster_spec))

        # Init Cluster object
        cl = self.make_cluster_object(cluster_name_required=False)
        builder = clusterbuilder.ClusterBuilder(cl)
        self._logger.info('Starting cluster')
        started = builder.start_cluster(profile['cluster_name'], cluster_spec, profile['central_logging_level'])
        if not started:
            return False, ''
        self._logger.info('Cluster "{0}" started'.format(profile['cluster_name']))

        message = ''
        # Launch environment if environment file is available
        if env_file:
            self._logger.info('Launching environment')
            try:
                env = environment.Environment(cl)
                # Launch environment (but wait 10 seconds for Mesos to init)
                success, message = env.launch_from_spec(env_file, 10)
                self._logger.info('Environment launched')
            except environment.Environment.LaunchError as e:
                self._logger.error(e)
                self._logger.error('Failed to launch environment')
                return False, message

        return True, message

    def launch_environment(self, environment_file):
        cl = self.make_cluster_object()

        try:
            env_file = EnvironmentFile(environment_file)
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

    def scale_nodes(self, action, num_nodes, node_name):
        cl = self.make_cluster_object()
        builder = clusterbuilder.ClusterBuilder(cl)
        delta = num_nodes
        actual_node_name = node_name
        if action == 'add':
            success, message, actual_node_name = builder.add_nodes(num_nodes, node_name)
        elif action == 'rm':
            success, message, actual_node_name = builder.rm_nodes(num_nodes, node_name)
            delta = -num_nodes
        else:
            raise ValueError('action must be either "add" or "rm"')

        env = environment.Environment(cl)
        if success and env.get_running_component_info():
            self._logger.info('Scaling running environment')
            success, message = env.scale_app(actual_node_name, delta, wait_time=60)

        return success, message


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

    def connect_to_container(self, component_name):
        # Check if component_name exists
        cl = self.make_cluster_object()
        env = environment.Environment(cl)
        running_apps = env.get_running_component_info()
        app = running_apps.get(component_name)
        if app is None:
            message = "Component '{0}' does not exist".format(component_name)
            return (False, message)

        if app > 1:
            message = "Cannot connect to '{0}' because there is more than one instance running on the cluster".format(component_name)
            return (False, message)

        return cl.connect_to_container(component_name)

    def central_logging(self):
        cl = self.make_cluster_object()
        return cl.central_logging()

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
        success = cl.workon()
        if success:
            message = 'Switched to {0}'.format(cluster_name)
        else:
            message = 'Could not switch to cluster {0}'.format(cluster_name)
        return success, message

    def terminate_cluster(self):
        cl = self.make_cluster_object()
        self._logger.info('Terminating cluster {0}'.format(cl.cluster_name))
        cl.terminate_cluster()
