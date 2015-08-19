import os
import yaml

"""
Module for storing default and static values
"""

DEFAULT_CONFIG_FILE = '~/.clusterous.yml'

local_config_dir = '~/.clusterous'
local_session_data_dir = local_config_dir + '/' + 'session'

current_controller_ip_file = local_config_dir + '/' + 'current_controller'
CLUSTER_INFO_FILE = local_config_dir + '/' + 'cluster_info.yml'

controller_ami_id = 'ami-2d6d2b17'
node_ami_id = 'ami-47eaad7d'
security_group_name_format = '{0}-sg'
controller_name_format = '{0}_controller'
controller_instance_type = 't2.small'
node_name_format = '{0}_node'
registry_s3_path = '/docker-registry'
central_logging_name_format = '{0}_central_logging'
central_logging_instance_type = 't2.small'
central_logging_ami_id = 'ami-45eaad7f'

shared_volume_path = '/home/data/'

remote_scripts_dir = 'ansible/remote'

default_cluster_def_filename = 'default_cluster.yml'

remote_host_scripts_dir = 'clusterous'
remote_host_key_file = 'key.pem'
remote_host_vars_file = 'vars.yml'
container_id_script_file = 'container_id.sh'

node_tag_status_uninitialized = 'uninitialized'
node_tag_status_initialized = 'initialized'

mesos_port = 5050
marathon_port = 8080
central_logging_port = 8999

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
