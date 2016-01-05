# Copyright 2015 Nicta
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import re

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

current_nat_ip_file = local_config_dir + '/' + 'current_controller'
cluster_info_file = local_config_dir + '/' + 'cluster_info.yml'


taggable_name_re = re.compile('^[\w-]+$')       # For user supplied strings such as cluster name
taggable_name_max_length = 64       # Arbitrary but ample, keeping in mind AWS keys can be max 127 chars

nat_name_format = '{0}-nat'
nat_name_tag_value = 'nat'
nat_instance_type = 't2.micro'
controller_name_format = '{0}-controller'
controller_name_tag_value = 'controller'
controller_instance_type = 't2.small'
node_name_format = '{0}-node-{1}'
instance_tag_key = '@clusterous'
instance_node_type_tag_key = 'NodeType'
registry_s3_path = '/docker-registry'
central_logging_name_format = '{0}-central-logging'
central_logging_name_tag_value = 'central-logging'
central_logging_instance_type = 't2.small'
central_logging_ami_id = 'ami-45eaad7f'
nat_ami_id = 'ami-e7ee9edd'
controller_ami_id = 'ami-fd4708c7'
node_ami_id = 'ami-47eaad7d'
default_zone = 'a'

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
nat_ssh_port_forwarding = 22000

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
