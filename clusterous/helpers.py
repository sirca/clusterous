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

import subprocess
import tempfile
import sys
import os
import yaml
import logging
import collections

from sshtunnel import SSHTunnelForwarder
import sshtunnel
from defaults import get_script, nat_ssh_port_forwarding


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

        args = ['ansible-playbook', '-i', hosts_file,
                '--private-key', key_file,
                '-c', 'ssh',
                '--extra-vars', '@{0}'.format(vars_file), playbook_file]
        # print ' '.join(args)
        process = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=run_env)
        output, error = process.communicate()

        if process.returncode != 0:
            logger.error('Ansible exited with code {0} when running {1}'.format(process.returncode, playbook_file))
            logger.info(output)
            logger.error(error)
            raise AnsibleHelper.AnsibleError(playbook_file, process.returncode, output, error)

        return process.returncode


SchemaEntry = collections.namedtuple('SchemaEntry', ['mandatory', 'default', 'type', 'schema'])

def validate(d, schema, strict=True):
    """
    Runs validation on d, according to schema, returns a validated dict.
    schema is a dictionary mapping field name (key) to a SchemaEntry.
    If strict is True, all keys in d must be described in schema. If not,
    d may contain keys not required by schema.
    """

    copy = d

    # First verify schema
    for key, rules in schema.iteritems():
        if key not in copy:
            if rules.mandatory:
                return False, 'Missing mandatory field "{0}"'.format(key), {}
            elif not rules.mandatory:
                copy[key] = rules.default
        elif key in copy:
            if type(copy[key]) == type(None):
                return False, 'A valid value must be provided for field "{0}"'.format(key), {}
            if not rules.type == type(copy[key]):
                return False, 'For field "{0}", expected type "{1}", got "{2}"'.format(key, rules.type.__name__, type(copy[key]).__name__), {}
            if rules.type == dict and rules.schema:
                # Recursively validate this nested dictionary
                success, message, validated = validate(copy[key], rules.schema, strict)
                if not success:
                    return False, 'In {0}: {1}'.format(key, message), {}
                else:
                    copy[key] = validated


    if strict:
        for key, val in d.iteritems():
            if key not in schema:
                return False, 'Unexpected field "{0}"'.format(key), {}

    return True, '', copy


class NoWorkingClusterException(Exception):
    pass

class SSHTunnel(object):
    class TunnelException(Exception):
        pass

    def __init__(self, host, username, key_file, remote_port, host_port=nat_ssh_port_forwarding):
        """
        Returns tuple consisting of local port and sshtunnel SSHTunnelForwarder object.
        Caller must call stop() on object when finished
        """
        logger = logging.getLogger('sshtunnel')
        logger.setLevel(logging.ERROR)

        try:
            self._server = SSHTunnelForwarder((host, host_port),
                    ssh_username=username, ssh_private_key=key_file,
                    remote_bind_address=('127.0.0.1', remote_port), logger=logger)
        except sshtunnel.BaseSSHTunnelForwarderError as e:
            raise self.TunnelException(e)


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
