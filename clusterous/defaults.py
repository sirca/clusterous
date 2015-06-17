import os

"""
Module for storing default and static values
"""

DEFAULT_CONFIG_FILE = '~/.clusterous.yml'

local_config_dir = '~/.clusterous'
current_controller_ip_file = local_config_dir + '/' + 'current_controller'

controller_ami_id = 'ami-25542f1f'
node_ami_id = 'ami-334b3009'
security_group_name_format = '{0}-sg'
controller_name_format = '{0}_controller'
controller_instance_type = 't2.small'
node_name_format = '{0}_node'
registry_s3_bucket = 'clusterous-docker-registry'
registry_s3_path = '/dev'

remote_scripts_dir = 'ansible/remote'

remote_host_scripts_dir = 'clusterous'
remote_host_key_file = 'key.pem'
remote_host_vars_file = 'vars.yml'

node_tag_status_uninitialized = 'uninitialized'
node_tag_status_initialized = 'initialized'
