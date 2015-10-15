import yaml
import os
import sys
import logging
import logging.config
import re

import boto

import defaults
import cluster
import clusterbuilder
from environmentfile import EnvironmentFile
import environmentfile

import environment
import helpers
from helpers import SchemaEntry


class FileError(Exception):
    def __init__(self, message, filename=''):
        super(FileError, self).__init__(message)
        self.filename = filename

class ConfigError(FileError):
    pass

class EnvironmentFileError(FileError):
    pass

class ProfileError(Exception):
    pass

class Clusterous(object):
    """
    Clusterous application
    """

    def __init__(self, config_file=defaults.DEFAULT_CONFIG_FILE):
        self.clusters = []
        self._config = {}
        self._cluster_class = None

        self._logger = logging.getLogger(__name__)

        self._read_config(config_file)

        conf_dir = os.path.expanduser(defaults.local_config_dir)
        if not os.path.exists(conf_dir):
            os.makedirs(conf_dir)

    def _read_config(self, config_file):
        """
        Read and validate global configuration
        """
        try:
            stream = open(os.path.expanduser(config_file), 'r')
            contents = yaml.load(stream)
            stream.close()
        except IOError as e:
            raise ConfigError(str(e), config_file)
        except yaml.YAMLError as e:
            raise ConfigError('Invalid YAML format: ' + str(e), config_file)

        cluster_class, message, fields = cluster.read_config(contents)

        if not cluster_class:
            raise ConfigError(message, config_file)

        self._config = fields
        self._cluster_class = cluster_class

    def _read_profile(self, profile_file):
        """
        Given user supplied file path, read in and validate profile file.
        Return dictionary contents
        """
        full_path = os.path.abspath(os.path.expanduser(profile_file))
        if not os.path.isfile(full_path):
            raise ProfileError('Cannot open file "{0}"'.format(profile_file))
        stream = open(full_path, 'r')
        try:
            contents = yaml.load(stream)
        except yaml.YAMLError as e:
            raise ProfileError('Invalid YAML format {0}'.format(e))

        main_schema = {
            'cluster_name': SchemaEntry(True, None, str, None),
            'controller_instance_type': SchemaEntry(False, '', str, None),
            'shared_volume_size': SchemaEntry(False, 0, int, None),
            'central_logging_level': SchemaEntry(False, 0, int, None),
            'environment_file': SchemaEntry(False, '', str, None),
            'shared_volume_id': SchemaEntry(False, '', str, None),
            'parameters': SchemaEntry(True, {}, dict, None)
        }


        # Validate profile file
        is_valid, message, validated = helpers.validate(contents, main_schema)

        if not is_valid:
            raise ProfileError(message)

        if not defaults.taggable_name_re.match(validated['cluster_name']):
            raise ProfileError('Unsupported characters in cluster_name "{0}"'.format(validated['cluster_name']))
        if len(validated['cluster_name']) > defaults.taggable_name_max_length:
            raise ProfileError('"cluster_name" cannot be more than {0} characters'.format(defaults.taggable_name_max_length))

        if not 0 <= validated['central_logging_level'] <= 2:
            raise ProfileError('"central_logging_level" must be either 0, 1 or 2')

        if validated['shared_volume_size'] < 0:
            raise ProfileError('"shared_volume_size" cannot be negative')

        return validated

    def make_cluster_object(self, cluster_name=None, cluster_name_required=True):
        if not (self._cluster_class and self._config):
            return None
        else:
            return self._cluster_class(self._config, cluster_name, cluster_name_required)


    def start_cluster(self, profile_file, launch_env=True):
        """
        Create a new cluster from profile file
        """
        profile = self._read_profile(profile_file)
        env_file = None
        cluster_spec = None

        try:
            if profile['environment_file']:
                env_file = EnvironmentFile(profile['environment_file'], profile['parameters'], profile_file)

            # If necessary, obtain cluster spec
            if not env_file or (not env_file.spec['cluster']):
                default_file_path = defaults.get_script(defaults.default_cluster_def_filename)
                cluster_env_file = EnvironmentFile(default_file_path, profile['parameters'])
                cluster_spec = cluster_env_file.spec['cluster']
            else:
                cluster_spec = env_file.spec['cluster']

        except environmentfile.UnknownValue as e:
            # If unknown value found, probably an error in the profile (i.e. user params)
            raise ProfileError(str(e))
        except environmentfile.EnvironmentSpecError as e:
            # Otherwise it's a problem in the environment file itself
            raise EnvironmentFileError(str(e), filename=profile['environment_file'])


        self._logger.debug('Actual cluster spec: {0}'.format(cluster_spec))

        # Init Cluster object
        cl = self.make_cluster_object(cluster_name_required=False)

        builder = clusterbuilder.ClusterBuilder(cl)
        self._logger.info('Starting cluster...')
        started = builder.start_cluster(profile['cluster_name'], cluster_spec, profile['central_logging_level'],
                                        profile['shared_volume_size'], profile['controller_instance_type'], profile['shared_volume_id'])

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
        except environmentfile.EnvironmentSpecError as e:
            raise EnvironmentFileError(e, filename=environment_file)
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
        return cl.connect_to_central_logging()

    def cluster_status(self):
        cl = self.make_cluster_object()
        env = environment.Environment(cl)
        info = cl.get_cluster_info()
        component_info =  env.get_running_components_by_node()

        # Fill in information about running components
        for node in info.get('nodes', {}):
            components = []
            for c in component_info.get(node, []):
                component = {}
                component['name'] = c.get('app_id', '').strip('/')
                component['count'] = c.get('instance_count', 0)
                components.append(component)
            info['nodes'][node]['components'] = components


        # Add information about shared volume usage
        info['shared_volume'] = cl.get_shared_volume_usage_info()

        return True, info

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

    def terminate_cluster(self, leave_shared_volume, force_delete_shared_volume):
        cl = self.make_cluster_object()
        self._logger.info('Terminating cluster {0}'.format(cl.cluster_name))
        cl.terminate_cluster(leave_shared_volume, force_delete_shared_volume)

    def ls_shared_volumes(self):
        """
        List available shared volumes left on cluster termination
        """
        cl = self.make_cluster_object()
        return (True, cl.ls_shared_volumes())
