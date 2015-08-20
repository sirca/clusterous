import subprocess
import tempfile
import sys
import os
import yaml
import logging

from sshtunnel import SSHTunnelForwarder
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

        if 'ANSIBLE_HOST_KEY_CHECKING' not in run_env:
            run_env['ANSIBLE_HOST_KEY_CHECKING']='False'

        if 'LOCAL_ANSIBLE_PYTHON_INTERPRETER' not in run_env:
            for python_version in ['python2', 'python']:
                process = subprocess.Popen(['which',python_version], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                output, error = process.communicate()
                if output:
                    run_env['ANSIBLE_HOST_KEY_CHECKING']=output
                    break

        args = ['ansible-playbook', '-i', hosts_file,
                '--private-key', key_file,
                '-c', 'ssh',
                '--extra-vars', '@{0}'.format(vars_file), playbook_file]
        # logger.debug(' '.join(args))
        process = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=run_env)
        output, error = process.communicate()

        if process.returncode != 0:
            logger.error('Ansible exited with code {0} when running {1}'.format(process.returncode, playbook_file))
            logger.info(output)
            logger.error(error)
            raise AnsibleHelper.AnsibleError(playbook_file, process.returncode, output, error)

        return process.returncode


class NoWorkingClusterException(Exception):
    pass

class SSHTunnel(object):
    def __init__(self, host, username, key_file, remote_port, host_port=22):
        """
        Returns tuple consisting of local port and sshtunnel SSHTunnelForwarder object.
        Caller must call stop() on object when finished
        """
        logger = logging.getLogger('sshtunnel')
        logger.setLevel(logging.ERROR)

        self._server = SSHTunnelForwarder((host, host_port),
                ssh_username=username, ssh_private_key=key_file,
                remote_bind_address=('127.0.0.1', remote_port), logger=logger)

    def connect(self):
        self._server.start()
        self.local_port = self._server.local_bind_port

    def close(self):
        self._server.stop()

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, type, value, traceback):
        self.close()
