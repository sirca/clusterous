import os
import yaml

"""
Module for storing default and static values
"""

DEFAULT_CONFIG_FILE = '~/.clusterous.yml'

local_config_dir = '~/.clusterous'
current_controller_ip_file = local_config_dir + '/' + 'current_controller'
CLUSTER_INFO_FILE = local_config_dir + '/' + 'cluster_info.yml'

controller_ami_id = 'ami-d3e4a3e9'
node_ami_id = 'ami-d1e4a3eb'
security_group_name_format = '{0}-sg'
controller_name_format = '{0}_controller'
controller_instance_type = 't2.small'
node_name_format = '{0}_node'
registry_s3_path = '/docker-registry'

remote_scripts_dir = 'ansible/remote'

remote_host_scripts_dir = 'clusterous'
remote_host_key_file = 'key.pem'
remote_host_vars_file = 'vars.yml'

node_tag_status_uninitialized = 'uninitialized'
node_tag_status_initialized = 'initialized'

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
