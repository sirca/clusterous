import subprocess
import tempfile
import sys
import os
import yaml
import logging
from defaults import get_script


class AnsibleHelper(object):

    class AnsibleError(Exception):
        def __init__(self, playbook, exit_code, output, error):
            self.playbook = playbook
            self.exit_code = exit_code
            self.output = output
            self.error = error

        def __str__(self):
            return self.error

    @staticmethod
    def run_playbook(playbook_file, vars_file, key_file, hosts_file=None, env=None):
        logger = logging.getLogger()
        if hosts_file == None:
            # Default
            hosts_file = get_script('ansible/hosts')

        run_env = os.environ.copy()
        if env != None:
            run_env.update(env)

        args = ['ansible-playbook', '-i', hosts_file,
                '--private-key', key_file,
                '--extra-vars', '@{0}'.format(vars_file), playbook_file]
        # logger.debug(' '.join(args))
        process = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=run_env)
        output, error = process.communicate()

        if process.returncode != 0:
            logger.error('Ansible exited with code {0} when running {1}'.format(process.returncode, playbook_file))
            logger.debug(output)
            logger.error(error)
            raise AnsibleHelper.AnsibleError(playbook_file, process.returncode, output, error)

        return process.returncode
