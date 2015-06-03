import os

"""
Module storing default and static values
"""




DEFAULT_CONFIG_FILE = '~/.clusterous.yml'


controller_ami_id = 'ami-472b547d'
node_ami_id = 'ami-5678'
security_group_name_format = '{0}-sg'
controller_name_format = '{0}_controller'
controller_instance_type = 'c3.large'   #'t2.medium'

def get_script(filename):
    """
    Takes script relative filename, returns absolute path
    Assumes this file is in Clusterous source root, uses __file__
    """
    return '{0}/{1}/{2}'.format(os.path.dirname(__file__), 'scripts', filename)