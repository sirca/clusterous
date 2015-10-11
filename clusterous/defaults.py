import os
import yaml

"""
Module for storing default and static values
"""

DEFAULT_CONFIG_FILE = '~/.clusterous.yml'

local_config_dir = '~/.clusterous'
local_session_data_dir = local_config_dir + '/' + 'session'
local_environment_dir = local_config_dir + '/' + 'environment'
cached_cluster_file = 'cluster_spec.yml'
cached_environment_file = 'environment.yml'
cached_cluster_file_path = local_environment_dir + '/' + cached_cluster_file
cached_environment_file_path = local_environment_dir + '/' + cached_environment_file

remote_environment_dir = '/root/environment'


current_controller_ip_file = local_config_dir + '/' + 'current_controller'
cluster_info_file = local_config_dir + '/' + 'cluster_info.yml'

controller_ami_id = 'ami-fd4708c7'
node_ami_id = 'ami-47eaad7d'
security_group_name_format = '{0}-sg'
controller_name_format = '{0}-controller'
controller_instance_type = 't2.small'
node_name_format = '{0}-node-{1}'
instance_tag_key = '@clusterous'
registry_s3_path = '/docker-registry'
central_logging_name_format = '{0}-central-logging'
central_logging_instance_type = 't2.small'
central_logging_ami_id = 'ami-45eaad7f'

controller_root_volume_size = 10    # GB

shared_volume_path = '/home/data/'
shared_volume_size = 20     # GB

remote_scripts_dir = 'ansible/remote'

default_cluster_def_filename = 'default_cluster.yml'

remote_host_scripts_dir = 'clusterous'
remote_host_key_file = 'key.pem'
remote_host_vars_file = 'vars.yml'
container_id_script_file = 'container_id.sh'

mesos_port = 5050
marathon_port = 8080
central_logging_port = 8081

# How many seconds to wait for all Marathon applications to reach "started" state
# Currently 30 minutes
app_launch_start_timeout = 1800

app_destroy_timeout = 60

def get_script(filename):
    """
    Takes script relative filename, returns absolute path
    Assumes this file is in Clusterous source root, uses __file__
    """
    return '{0}/{1}/{2}'.format(os.path.dirname(__file__), 'scripts', filename)

def get_remote_dir():
    """
    Return full path of remote scripts directory
    """
    return '{0}/{1}/{2}'.format(os.path.dirname(__file__), 'scripts', remote_scripts_dir)
