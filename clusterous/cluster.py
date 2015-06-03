import subprocess
import tempfile
import sys
import yaml

import defaults
from defaults import get_script


class AnsibleHelper(object):
    @staticmethod
    def run_playbook(playbook_file, vars_file, key_file, hosts_file=None):
        if hosts_file == None:
            # Default
            hosts_file = get_script('ansible/hosts')

        args = ['ansible-playbook', '-i', hosts_file,
                '--private-key', key_file,
                '--extra-vars', '@{0}'.format(vars_file), playbook_file]
        print ' '.join(args)
        process = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output, error = process.communicate()
        
        print output
        print error
        if process.returncode != 0:
            print >> sys.stderr, error

        return process.returncode

class Cluster(object):
    def __init__(self, config):
        self._config = config['AWS']
        self._running = False



    def _prepare_vars_dict(self, cluster_name):
        return {
                'AWS_KEY': self._config['access_key_id'],
                'AWS_SECRET': self._config['secret_access_key'],
                'region': self._config['region'],
                'keypair': self._config['key_pair'],
                'vpc_id': self._config['vpc_id'],
                'vpc_subnet_id': self._config['subnet_id'],
                'cluster_name': cluster_name,
                'security_group_name': defaults.security_group_name_format.format(cluster_name),
                'controller_ami_id': defaults.controller_ami_id,
                'controller_instance_name': defaults.controller_name_format.format(cluster_name),
                'controller_instance_type': defaults.controller_instance_type,
                'node_ami_id': defaults.node_ami_id,
                }

    def init_cluster(self, cluster_name):
        """
        Initialise security group(s), cluster controller etc
        """
        vars_dict = self._prepare_vars_dict(cluster_name)

        print yaml.dump(vars_dict, default_flow_style=False)

        vars_file = tempfile.NamedTemporaryFile()
        vars_file.write(yaml.dump(vars_dict, default_flow_style=False))
        vars_file.flush()

        # Run ansible
        print "Creating security group"
        AnsibleHelper.run_playbook(get_script('ansible/01_create_sg.yml'),
                                   vars_file.name, self._config['key_file'])
        print "Launching cluster"
        AnsibleHelper.run_playbook(get_script('ansible/02_create_master.yml'),
                                   vars_file.name, self._config['key_file'])
        print "Done"

        vars_file.close()

        # template = open(defaults.ANSIBLE_VARS_TEMPLATE, 'r')
        # template_string = template.read()
        # template.close()

        # playbook_string = template_string.format(**vars)
        # print playbook_string



        # print vars_file.name



        