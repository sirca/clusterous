import os

"""
Module for storing default and static values
"""

DEFAULT_CONFIG_FILE = '~/.clusterous.yml'


controller_ami_id = 'ami-6dafd757'
node_ami_id = 'ami-01afd73b'
security_group_name_format = '{0}-sg'
controller_name_format = '{0}_controller'
controller_instance_type = 't2.small'
node_name_format = '{0}_node'
registry_s3_bucket = 'bdkd-docker-registry'
registry_s3_path = '/dev'


def get_script(filename):
    """
    Takes script relative filename, returns absolute path
    Assumes this file is in Clusterous source root, uses __file__
    """
    return '{0}/{1}/{2}'.format(os.path.dirname(__file__), 'scripts', filename)