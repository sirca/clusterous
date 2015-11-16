import subprocess
import tempfile
import sys
import os
import yaml
import logging
import time
import glob
import shutil
import json
import stat
import re
import errno
from datetime import datetime
from collections import namedtuple

from dateutil import parser, tz
import boto.ec2
import boto.vpc
import boto.s3.connection
import paramiko

import defaults
from defaults import get_script
from helpers import AnsibleHelper, SSHTunnel, NoWorkingClusterException

# TODO: Move to another module as appropriate, as this is very general purpose
def retry_till_true(func, sleep_interval, timeout_secs=300):
    """
    Call func repeatedly, with an interval of sleep_interval, for up to
    timeout_secs seconds, until func returns true.

    Returns true if succesful, false if timeout occurs
    """
    success = True
    start_time = time.time()
    while not func():
        if time.time() >= start_time + timeout_secs:
            success = False
            break
        time.sleep(sleep_interval)

    return success


def read_config(config):
    """
    Reads in config (from config file), validates,
    and returns appropriate Cluster subclass, error message (if any), and fields
    """
    valid = isinstance(config, list) and len(config) > 0 and isinstance(config[0], dict) and len(config[0]) > 0

    if not valid:
        return None, 'Invalid structure', None

    # TODO: generalise when support for multiple cluster types is added
    cluster_type = config[0].keys()[0]
    if not isinstance(config[0][cluster_type], dict):
        return None, 'Invalid structure, expected fields under cluster type', None

    if cluster_type == 'AWS':
        success, message = AWSCluster.validate_config(config[0]['AWS'])
        if success:
            return AWSCluster, message, config[0]['AWS']
        else:
            return None, message, None
    else:
        return None, 'Unknown cluster type "{0}"'.format(cluster_type), None


class ClusterException(Exception):
    """
    Unrecoverable error, e.g. when creating a cluster
    """
    pass

class Cluster(object):
    """
    Represents infrastrucure aspects of the cluster. Includes high level operations
    for setting up cluster controller, launching application nodes etc.

    Prepares cluster to a stage where applications can be run on it
    """
    def __init__(self, config, cluster_name=None, cluster_name_required=True):
        self._config = config
        self._running = False
        self._logger = logging.getLogger(__name__)
        self._controller_ip = ''
        if cluster_name_required and not cluster_name:
            name = self._get_working_cluster_name()
            if not name:
                message = 'No working cluster has been set.'
                self._logger.error(message)
                raise NoWorkingClusterException(message)
            self.cluster_name = name
        elif cluster_name:
            self.cluster_name = cluster_name


    def _get_cluster_info(self):
        cluster_info_file = os.path.expanduser(defaults.cluster_info_file)
        if not os.path.isfile(cluster_info_file):
            return None

        f = open(os.path.expanduser(cluster_info_file), 'r')
        cluster_info = yaml.load(f)
        return cluster_info

    @staticmethod
    def validate_config(fields):
        pass

    def _get_working_cluster_name(self):
        cluster_info = self._get_cluster_info()
        if not cluster_info:
            return None
        return cluster_info.get('cluster_name')

    def _get_logging_vars(self):
        info = self._get_cluster_info()

        logging_vars = {}
        logging_vars['central_logging_level'] = info.get('central_logging_level', 0)
        logging_vars['central_logging_ip'] = info.get('central_logging_ip', '')

        return logging_vars


    def _get_controller_ip(self):
        if self._controller_ip:
            return self._controller_ip

        info = self._get_cluster_info()

        return info.get('controller_ip', None)

    def controller_tunnel(self, remote_port):
        """
        Returns helpers.SSHTunnel object connected to remote_port on controller
        """
        pass

    def init_cluster(self, cluster_name):
        pass

    def launch_nodes(self, num_nodes, instance_type):
        pass

    def _ssh_to_controller(self):
        raise NotImplementedError('SSH connections are specific to cloud providers')


class AWSCluster(Cluster):

    @staticmethod
    def _validate_s3_bucket_name(name):
        """
        Validates name of an S3 bucket, ensuring compliance with most of the
        restrictions described by Amazon:
        http://docs.aws.amazon.com/AmazonS3/latest/dev/BucketRestrictions.html
        In addition, Clusterous doesn't allow dots in S3 bucket names to avoid
        SSL issues.

        Returns 2-tuple in the form (success, message)
        """
        s3_re = re.compile('^[a-z0-9][a-z0-9-]+$')

        if '.' in name:
            return False, 'Dots in bucket name not supported'

        if not 3 <= len(name) <= 63:
            return False, 'Must be between 3 and 63 characters long (inclusive)'

        if not s3_re.search(name):
            return False, 'Contains invalid characters'

        return True, ''

    @staticmethod
    def validate_config(fields):
        mandatory_fields = ['access_key_id', 'secret_access_key', 'key_pair', 'key_file',
                            'vpc_id', 'clusterous_s3_bucket', 'subnet_id', 'region']

        vpc_re = re.compile('^vpc-\w+$')
        subnet_re = re.compile('^subnet-\w+$')

        # Check for unrecognised fields
        unrecog_fields = []
        for f in fields.keys():
            if not f in mandatory_fields:
                unrecog_fields.append(f)

        if unrecog_fields:
            unrecog_str = ', '.join(unrecog_fields)
            return False, 'The following fields are unrecognised: {0}'.format(unrecog_str)

        # Check for missing mandatory fields
        missing_fields = []
        for f in mandatory_fields:
            if not f in fields or not fields[f]:
                missing_fields.append(f)

        if missing_fields:
            missing_str = ', '.join(missing_fields)
            return False, 'The following field(s) must be supplied with valid values: {0}'.format(missing_str)


        # Validate individual fields
        key_file = os.path.expanduser(fields['key_file'])
        if not os.path.isfile(key_file):
            message = 'Cannot find key file "{0}"'.format(fields['key_file'])
            return False, message

        if oct(stat.S_IMODE(os.stat(key_file).st_mode)) != '0600':
            message = 'Key file {0} must have permissions of 600 (not readable by others)'.format(fields['key_file'])
            return False, message

        s3_valid, s3_msg = AWSCluster._validate_s3_bucket_name(fields['clusterous_s3_bucket'])
        if not s3_valid:
            message = 'Error in S3 bucket name "{0}": {1}'.format(fields['clusterous_s3_bucket'], s3_msg)
            return False, message

        if not vpc_re.search(fields['vpc_id']):
            return False, 'vpc_id "{0}" is not in valid format'.format(fields['vpc_id'])

        if not subnet_re.search(fields['subnet_id']):
            return False, 'subnet_id "{0}" is not in valid format'.format(fields['subnet_id'])

        return True, ''


    def _controller_vars_dict(self):
        return {
                'AWS_KEY': self._config['access_key_id'],
                'AWS_SECRET': self._config['secret_access_key'],
                'clusterous_s3_bucket': self._config['clusterous_s3_bucket'],
                'registry_s3_path': defaults.registry_s3_path,
                'remote_scripts_dir': defaults.get_remote_dir(),
                'remote_host_scripts_dir': defaults.remote_host_scripts_dir,
                'central_logging_instance_name': defaults.central_logging_name_format.format(self.cluster_name),
                'central_logging_ami_id': defaults.central_logging_ami_id,
                'central_logging_instance_type': defaults.central_logging_instance_type,
                }

    def _ansible_env_credentials(self):
        return {
                'AWS_ACCESS_KEY_ID': self._config['access_key_id'],
                'AWS_SECRET_ACCESS_KEY': self._config['secret_access_key']
                }

    def _make_vars_file(self, vars_dict):
        if not vars_dict:
            vars_d = {}
        else:
            vars_d = vars_dict
        vars_file = tempfile.NamedTemporaryFile()
        vars_file.write(yaml.safe_dump(vars_d, default_flow_style=False))
        vars_file.flush()
        return vars_file

    def _run_on_controller(self, playbook, hosts_file, remote_vars={}):

        remote_vars_file = self._make_vars_file(remote_vars)

        local_vars = {
                'key_file_src': self._config['key_file'],
                'key_file_name': defaults.remote_host_key_file,
                'hosts_file_src': hosts_file,
                'hosts_file_name': os.path.basename(hosts_file),
                'vars_file_src': remote_vars_file.name,
                'vars_file_name': os.path.basename(remote_vars_file.name),
                'remote_dir': defaults.remote_host_scripts_dir,
                'playbook_file': playbook
                }

        local_vars_file = self._make_vars_file(local_vars)

        AnsibleHelper.run_playbook(get_script('ansible/run_remote.yml'),
                      local_vars_file.name, self._config['key_file'],
                      hosts_file=os.path.expanduser(defaults.current_controller_ip_file))

        local_vars_file.close()
        remote_vars_file.close()

    def _get_instances(self, cluster_name, connection=None):
        if not connection:
            conn = boto.ec2.connect_to_region(self._config['region'],
                        aws_access_key_id=self._config['access_key_id'],
                        aws_secret_access_key=self._config['secret_access_key'])
            if not conn:
                raise ClusterException('Cannot connect to AWS')
        else:
            conn = connection

        # Get instances
        instance_filters = { 'tag:{0}'.format(defaults.instance_tag_key):
                        [cluster_name],
                        'instance-state-name': ['running', 'pending', 'stopping', 'shutting-down']
                        }
        instance_list = conn.get_only_instances(filters=instance_filters)
        return instance_list

    def _get_node_instances(self, conn, node_name):
        """
        Get only instances matching given node name (e.g. "worker")
        """
        name_tag = defaults.node_name_format.format(self.cluster_name, node_name)
        instance_filters = { 'tag:Name': [name_tag],
                        'instance-state-name': ['running', 'pending', 'stopping']
                        }
        instance_list = conn.get_only_instances(filters=instance_filters)
        return instance_list

    def _ssh_to_controller(self):
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(hostname = self._get_controller_ip(),
                        username = 'root',
                        key_filename = os.path.expanduser(self._config['key_file']))
        except paramiko.AuthenticationException as e:
            self._logger.error('Could not connect to controller')
            raise e

        return ssh

    def get_central_logging_ip(self):
        instances = self._get_instances(self.cluster_name)
        ip = None
        for instance in instances:
            if defaults.central_logging_name_format.format(self.cluster_name) in instance.tags['Name']:
                ip = str(instance.private_ip_address)
                break
        return ip

    def store_file_on_controller(self, remote_file_path, source_file):
        ssh = self._ssh_to_controller()
        sftp = ssh.open_sftp()
        sftp.put(os.path.expanduser(self._config['key_file']), remote_key_path)
        sftp.mkdir(os.path.dirname(remote_file_path))
        sftp.put(source_file, remote_file_path, confirm=True)
        sftp.close()

    def make_controller_tunnel(self, remote_port):
        """
        Returns helpers.SSHTunnel object connected to remote_port on controller
        """
        return SSHTunnel(self._get_controller_ip(), 'root',
                os.path.expanduser(self._config['key_file']), remote_port)

    def make_tunnel_on_controller(self, controller_port, remote_host, remote_port):
        """
        Create an ssh tunnel from the controller to a cluster node. Note that this
        doesn't expose a port on the local machine
        """
        remote_key_path = '/root/{0}'.format(os.path.basename(self._config['key_file']))

        ssh_sock_file = '/tmp/clusterous_tunnel_%h_{0}.sock'.format(controller_port)
        create_cmd = ('ssh -4 -i {0} -f -N -M -S {1} -o ExitOnForwardFailure=yes ' +
              '-o StrictHostKeyChecking=no ' +
              'root@{2} -L {3}:127.0.0.1:{4}').format(remote_key_path,
              ssh_sock_file, remote_host, controller_port,
              remote_port)


        destroy_cmd = 'ssh -S {0} -O exit {1}'.format(ssh_sock_file, remote_host)

        ssh = self._ssh_to_controller()
        sftp = ssh.open_sftp()
        sftp.put(os.path.expanduser(self._config['key_file']), remote_key_path)
        sftp.chmod(remote_key_path, stat.S_IRUSR | stat.S_IWUSR)
        sftp.close()

        # First ensure that any previously created tunnel is destroyed
        stdin, stdout, stderr = ssh.exec_command(destroy_cmd)
        # Create tunnel
        stdin, stdout, stderr = ssh.exec_command(create_cmd)

        ssh.close()

    def create_permanent_tunnel_to_controller(self, remote_port, local_port, prefix=''):
        """
        Creates a persistent SSH tunnel from local machine to controller by running
        the ssh command in the background
        """

        key_file = os.path.expanduser(self._config['key_file'])

        # Useful to isolate user created sockets from our own
        prefix_str = 'clusterous' if not prefix else prefix

        # Temporary file containing ssh socket data
        ssh_sock_file = '{0}/{1}_tunnel_%h_{2}.sock'.format(
                        os.path.expanduser(defaults.local_session_data_dir),
                        prefix_str, local_port)

        # Ensure that any previously created tunnel is destroyed
        reset_cmd = ['ssh', '-S', ssh_sock_file, '-O', 'exit',
                self._get_controller_ip()]

        # Normal tunnel command
        connect_cmd = ['ssh', '-i', key_file, '-N', '-f', '-M',
                '-S', ssh_sock_file, '-o', 'ExitOnForwardFailure=yes',
                'root@{0}'.format(self._get_controller_ip()),
                '-L', '{0}:127.0.0.1:{1}'.format(local_port, remote_port)]

        # If socket file doesn't exist, it will return with an error. This is normal
        process = subprocess.Popen(reset_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=None)
        output, error = process.communicate()

        return_code = subprocess.call(connect_cmd)

        return True if return_code == 0 else False

    def delete_all_permanent_tunnels(self, delete_logging_tunnel=False):
        """
        Deletes all persistent SSH tunnels to the controller that were created by
        create_permanent_tunnel_to_controller()
        """
        key_file = os.path.expanduser(self._config['key_file'])

        sock_files = glob.glob('{0}/clusterous_tunnel_*.sock'.format(
                        os.path.expanduser(defaults.local_session_data_dir)))

        all_deleted = True
        for sock in sock_files:
            # Leave central logging tunnel
            if '_{0}.sock'.format(defaults.central_logging_port) in sock:
                if not delete_logging_tunnel:
                    continue

            reset_cmd = ['ssh', '-S', sock, '-O', 'exit',
                            self._get_controller_ip()]
            process = subprocess.Popen(reset_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=None)
            output, error = process.communicate()

            if process.returncode != 0:
                self._logger.warning('Problem deleting SSH tunnel at {0}'.format(sock))
                all_deleted = False

        return all_deleted

    def _create_security_group(self, cluster_name, conn):
        """
        Given a cluster name and Boto EC2 connection, creates a
        cluster security group (before deleting any existing one)
        and returns the SG id
        """
        sg_name = defaults.security_group_name_format.format(cluster_name)
        descr = 'Security group for {0}'.format(cluster_name)
        for s in conn.get_all_security_groups():
            if s.name == sg_name:
                self._logger.debug('Security group "{0}" already exists'.format(sg_name))
                return s.id
        sg = conn.create_security_group(sg_name, descr, vpc_id = self._config['vpc_id'])
        sg.add_tag(key='Name', value=sg_name)
        sg.add_tag(key=defaults.instance_tag_key, value=cluster_name)
        sg.authorize(ip_protocol='tcp', from_port='22', to_port='22', cidr_ip='0.0.0.0/0')
        sg.authorize(ip_protocol='tcp', from_port='80', to_port='80', cidr_ip='0.0.0.0/0')
        # Boto documentation is misleading: need to specify protocol to -1 to mean all protocols
        sg.authorize(ip_protocol=-1, src_group=sg)
        return sg.id

    def _get_current_sg_id(self, conn):
        """
        Given a connection object, return the id of the security
        group for current cluster. Returns None if zero or multiple matches
        """
        if not self.cluster_name:
            return None
        sg_name = defaults.security_group_name_format.format(self.cluster_name)
        sg_list = conn.get_all_security_groups(filters={'tag:Name':sg_name})
        if not sg_list or len(sg_list) != 1:
            # Returns None if no match, or multiple matches
            return None

        return sg_list[0].id


    def _wait_and_tag_instance_reservations(self, tag_and_inst_list, sleep_interval=5):
        launched = {}
        launched_ids = {}
        inst_list = []
        inst_to_tag = {}
        LaunchInfo = namedtuple('LaunchInfo', 'public_ips private_ips')
        for (label, tag, insts) in tag_and_inst_list:
            inst_list.extend(insts)
            for i in insts:
                inst_to_tag[i.id] = (label, tag)

        while len(launched_ids) < len(inst_list):
            time.sleep(sleep_interval)
            for inst in inst_list:
                if inst.state == 'running' and inst.id not in launched_ids:
                    if inst.ip_address:
                        launched_ids[inst.id] = True
                        label, tags = inst_to_tag[inst.id]
                        # Add default "clusterous" tag
                        t = tags.copy()
                        clusterous_tag = {defaults.instance_tag_key: self.cluster_name}
                        t.update(clusterous_tag)
                        inst.add_tags(t)
                        if not label in launched:
                            launched[label] = LaunchInfo([], [])
                        launched[label].public_ips.append(inst.ip_address)
                        launched[label].private_ips.append(inst.private_ip_address)
                        self._logger.debug('Running {0} {1} {2}'.format(inst.ip_address, tags, inst.id))
                # There is no good reason for this to happen in practice
                elif inst.state in ('terminated', 'stopped', 'stopping'):
                    self._logger.error('Instance {0} is in state "{1}"'.format(inst.id, inst.state))
                    self._logger.error('Problem creating instance')
                    # Unrecoverable error, exit to prevent infinite loop
                    return None
                else:
                    # Refresh instance data
                    inst.update()

        return launched

    def _write_to_hosts_file(self, filename, ips, group_name='', overwrite=False):
        """
        Given a destination absolute filename, a list of IPs, and a group name,
        create an Ansible inventory file, returning True on success
        """
        mode = 'w' if overwrite else 'a'
        with open(filename, mode) as f:
            if group_name:
                f.write('[{0}]\n'.format(group_name.strip()))
            for ip in ips:
                f.write('{0}\n'.format(ip.strip()))
        return True

    def _create_config_dirs(self):
        for directory in [defaults.local_config_dir, defaults.local_session_data_dir, defaults.local_environment_dir]:
            d = os.path.expanduser(directory)
            if not os.path.exists(d):
                os.makedirs(d)
        return

    def _copy_environment_to_controller(self):
        """
        Syncs locally cached environment file(s) to controller
        """
        ssh = self._ssh_to_controller()
        sftp = ssh.open_sftp()

        for f in [defaults.cached_cluster_file_path, defaults.cached_environment_file_path]:
            full_path = os.path.expanduser(f)
            if os.path.exists(full_path):
                try:
                    sftp.mkdir(defaults.remote_environment_dir)
                except IOError as e:
                    pass
                dest_path = defaults.remote_environment_dir + '/' + os.path.basename(full_path)
                sftp.put(full_path, dest_path, confirm=True)

        sftp.close()


    def _copy_environment_from_controller(self):
        """
        Syncs environment file(s) on controller to local cache
        """
        ssh = self._ssh_to_controller()
        sftp = ssh.open_sftp()
        for f in [defaults.cached_cluster_file_path, defaults.cached_environment_file_path]:
            local_path = os.path.expanduser(f)
            try:
                remote_path = defaults.remote_environment_dir + '/' + os.path.basename(local_path)
                sftp.get(remote_path, local_path)
            except IOError as e:
                # Only valid way to handle (valid) case where files don't exist on controller
                if e.errno != errno.ENOENT:     # No such file or directory error
                    raise e
        sftp.close()

    def get_cluster_spec(self):
        # Sync from controller
        self._copy_environment_from_controller()
        local_cluster_spec = os.path.expanduser(defaults.cached_cluster_file_path)
        node_types = []
        stream = open(local_cluster_spec, 'r')
        spec = yaml.load(stream)

        return spec


    def init_cluster(self, cluster_name, cluster_spec, nodes_info=[], logging_level=0,
                     shared_volume_size=None, controller_instance_type=None, shared_volume_id=None):
        """
        Initialise security group(s), cluster controller etc
        """
        self.cluster_name = cluster_name
        self._shared_volume_size = defaults.shared_volume_size if not shared_volume_size else shared_volume_size
        self._controller_instance_type = defaults.controller_instance_type if not controller_instance_type else controller_instance_type

        # Create dirs
        self._create_config_dirs()

        # Write cluster spec to local dir
        cluster_spec_file_name = os.path.expanduser(defaults.cached_cluster_file_path)
        with open(cluster_spec_file_name, 'w') as f:
            f.write(yaml.dump(cluster_spec))

        c = self._config

        conn = boto.ec2.connect_to_region(c['region'], aws_access_key_id=c['access_key_id'],
                                            aws_secret_access_key=c['secret_access_key'])
        if not conn:
            raise ClusterException('Cannot connect to AWS')

        # Check if cluster by this name is already running
        if self._get_instances(cluster_name, connection=conn):
            self._logger.error('A cluster by the name "{0}" is already running, cannot start'.format(cluster_name))
            raise ClusterException('Another cluster by the same name is running')

        # Create registry bucket if it doesn't already exist
        s3conn = boto.s3.connection.S3Connection(c['access_key_id'], c['secret_access_key'])
        if not s3conn.lookup(c['clusterous_s3_bucket']):
            try:
                self._logger.info('Creating S3 bucket')
                s3conn.create_bucket(c['clusterous_s3_bucket'], location=c['region'])
            except boto.exception.S3CreateError as e:
                self._logger.error('Unable to create S3 bucket due to an AWS conflict. Try again later.')
                self._logger.error(e)
                raise ClusterException('Unrecoverable error while trying to start cluster')

        # Shared volume
        if shared_volume_id:
            try:
                shared_volume = conn.get_all_volumes([shared_volume_id])[0]
                if shared_volume.status != 'available':
                    raise ClusterException('Volume "{0}" is not available'.format(shared_volume_id))
                vpc_conn = boto.vpc.connect_to_region(c['region'], aws_access_key_id=c['access_key_id'],aws_secret_access_key=c['secret_access_key'])
                subnet = vpc_conn.get_all_subnets([c['subnet_id']])[0]
                if subnet.availability_zone != shared_volume.zone:
                    raise ClusterException('Conflict on availability zone. Sub-net "{0}" in "{1}" and Volume "{2}" in "{3}"'.format(c['subnet_id'],
                                                                                                                            subnet.availability_zone,
                                                                                                                            shared_volume_id,
                                                                                                                            shared_volume.zone))
            except boto.exception.EC2ResponseError as e:
                raise ClusterException('Volume "{0}" does not exist'.format(shared_volume_id))
    
        # Create Security group
        self._logger.info('Creating security group')
        sg_id = self._create_security_group(cluster_name, conn)

        #
        # Launch all instances
        #

        # Launch controller
        self._logger.info('Starting controller')
        block_devices = boto.ec2.blockdevicemapping.BlockDeviceMapping(conn)
        root_vol = boto.ec2.blockdevicemapping.BlockDeviceType(connection=conn, delete_on_termination=True)
        root_vol.size = defaults.controller_root_volume_size

        block_devices['/dev/sda1'] = root_vol
        controller_res = conn.run_instances(defaults.controller_ami_id, min_count=1,
                                        key_name=c['key_pair'], instance_type=self._controller_instance_type,
                                        subnet_id=c['subnet_id'], block_device_map=block_devices, security_group_ids=[sg_id])

        controller_tags = {'Name': defaults.controller_name_format.format(cluster_name),
                            defaults.instance_node_type_tag_key: defaults.controller_name_tag_value}
        controller_tags_and_res = [('controller', controller_tags, controller_res.instances)]

        # Loop through node groups and launch all
        self._logger.info('Starting all nodes')
        node_tags_and_res = []
        for num_nodes, instance_type, node_tag in nodes_info:
            res = conn.run_instances(defaults.node_ami_id, min_count=num_nodes, max_count=num_nodes,
                                key_name=c['key_pair'], instance_type=instance_type,
                                subnet_id=c['subnet_id'], security_group_ids=[sg_id])
            node_tags = {'Name': defaults.node_name_format.format(cluster_name, node_tag),
                        defaults.instance_node_type_tag_key: node_tag}
            node_tags_and_res.append((node_tag, node_tags, res.instances))

        # Launch logging instance if necessary
        logging_tags_and_res = []
        if logging_level > 0:
            self._logger.info('Starting central logging instance')
            logging_res = conn.run_instances(defaults.central_logging_ami_id, min_count=1,
                                            key_name=c['key_pair'], instance_type=defaults.central_logging_instance_type,
                                            subnet_id=c['subnet_id'], block_device_map=block_devices, security_group_ids=[sg_id])
            logging_tags = {'Name': defaults.central_logging_name_format.format(cluster_name),
                            defaults.instance_node_type_tag_key: defaults.central_logging_name_tag_value}
            logging_tags_and_res = [('central-logging', logging_tags, logging_res.instances)]


        # Wait for controller to launch
        controller = self._wait_and_tag_instance_reservations(controller_tags_and_res)

        # Create cluster info file, so that user immediately has a working cluster set
        self._set_cluster_info({'controller_ip': controller.values()[0].public_ips[0], 'cluster_name': cluster_name})

        controller_inventory = os.path.expanduser(defaults.current_controller_ip_file)
        self._write_to_hosts_file(controller_inventory, [controller.values()[0].public_ips[0]], 'controller', overwrite=True)

        # Shared volume
        if shared_volume_id:
            # Attach shared volume
            self._logger.info('Attaching EBS volume "{0}"'.format(shared_volume_id))
            conn.attach_volume(shared_volume_id, controller_res.instances[0].id, "/dev/sdf")
            while conn.get_all_volumes([shared_volume_id])[0].status != 'in-use':
                time.sleep(2)
            conn.create_tags([shared_volume_id], {'Attached': cluster_name})
        else:
            # Create and attach shared volume
            self._logger.info('Creating shared volume')
            shared_vol = conn.create_volume(self._shared_volume_size, zone=controller_res.instances[0].placement)
            while shared_vol.status != 'available':
                time.sleep(2)
                shared_vol.update()
            self._logger.debug('Shared volume {0} created'.format(shared_vol.id))
            conn.create_tags([shared_vol.id], {'Name': defaults.controller_name_format.format(cluster_name),
                                               defaults.instance_tag_key: cluster_name})
    
            attach = shared_vol.attach(controller_res.instances[0].id, '/dev/sdf')
            while shared_vol.attachment_state() != 'attached':
                time.sleep(2)
                shared_vol.update()

        # Extra variables used by ansible scripts
        extra_vars = {'central_logging_level': logging_level, 
                      'central_logging_ip': '',
                      'byo_volume': 1 if shared_volume_id else 0
                      }

        # Configure controller
        controller_vars_dict = self._controller_vars_dict()
        controller_vars_dict.update(extra_vars)
        controller_vars_file = self._make_vars_file(controller_vars_dict)

        self._logger.info('Configuring controller instance...')
        AnsibleHelper.run_playbook(defaults.get_script('ansible/01_configure_controller.yml'),
                                   controller_vars_file.name, self._config['key_file'],
                                   hosts_file=controller_inventory)

        controller_vars_file.close()

        self._copy_environment_to_controller()


        # Wait for logging instance to launch and configure
        if logging_tags_and_res:
            self._logger.info('Configuring central logging...')
            central_logging = self._wait_and_tag_instance_reservations(logging_tags_and_res)
            extra_vars['central_logging_ip'] = central_logging.values()[0].private_ips[0]     # private ip
            logging_inventory = tempfile.NamedTemporaryFile()
            self._write_to_hosts_file(logging_inventory.name, [central_logging.values()[0].private_ips[0]], 'central-logging', overwrite=True)
            logging_inventory.flush()
            self._run_on_controller('configure_central_logging.yml', logging_inventory.name)
            logging_inventory.close()
        # Write logging vars to cluster info file
        self._set_cluster_info(extra_vars)


        # Configure nodes
        if node_tags_and_res:
            self._configure_nodes(nodes_info, node_tags_and_res, controller.values()[0].public_ips[0], extra_vars)

        # TODO: this is useful for debugging, but remove at a later stage
        self.create_permanent_tunnel_to_controller(8080, 8080, prefix='marathon')


    def _configure_nodes(self, nodes_info, node_tags_and_res, controller_ip, extra_vars={}):
        nodes = self._wait_and_tag_instance_reservations(node_tags_and_res)
        if not nodes:
            return False

        nodes_inventory = tempfile.NamedTemporaryFile()
        for num_nodes, instance_type, node_tag in nodes_info:
            self._write_to_hosts_file(nodes_inventory.name, nodes[node_tag].private_ips, node_tag, overwrite=False)
        nodes_inventory.flush()
        self._logger.info('Configuring nodes...')
        self._run_on_controller('configure_nodes.yml', nodes_inventory.name, extra_vars)
        nodes_inventory.close()
        return True

    def _set_cluster_info(self, info):
        """
        Writes information to cluster info file. info is a flat dictionary.
        Existing values are not removed; this method only add/updates values
        Returns True if everything goes well
        """
        cluster_info_file = os.path.expanduser(defaults.cluster_info_file)


        existing = {}
        if os.path.exists(cluster_info_file):
            stream = open(cluster_info_file, 'r')
            existing = yaml.load(stream)

        existing.update(info)

        stream = open(cluster_info_file, 'w')
        stream.write(yaml.dump(existing, default_flow_style=False))

        return True


    def add_nodes(self, num_nodes, instance_type, node_name):
        success = False
        self._logger.info('Creating {0} "{1}" nodes'.format(num_nodes, node_name))

        c = self._config
        nodes_info = [(num_nodes, instance_type, node_name)]
        controller_ip = self._get_controller_ip()
        logging_vars = self._get_logging_vars()

        conn = boto.ec2.connect_to_region(c['region'], aws_access_key_id=c['access_key_id'],
                                            aws_secret_access_key=c['secret_access_key'])
        if not conn:
            raise ClusterException('Cannot connect to AWS')


        sg_id = self._get_current_sg_id(conn)
        if not sg_id:
            return False

        res = conn.run_instances(defaults.node_ami_id, min_count=num_nodes, max_count=num_nodes,
                                key_name=c['key_pair'], instance_type=instance_type,
                                subnet_id=c['subnet_id'], security_group_ids=[sg_id])
        node_tags = {'Name': defaults.node_name_format.format(self.cluster_name, node_name),
                    defaults.instance_node_type_tag_key: node_name}
        node_tags_and_res = [(node_name, node_tags, res.instances)]

        self._logger.info('Waiting for nodes to start...')
        return self._configure_nodes(nodes_info, node_tags_and_res, controller_ip, logging_vars)

    def rm_nodes(self, num_nodes, node_name):
        c = self._config
        conn = boto.ec2.connect_to_region(c['region'], aws_access_key_id=c['access_key_id'],
                                            aws_secret_access_key=c['secret_access_key'])
        if not conn:
            raise ClusterException('Cannot connect to AWS')


        instance_list = self._get_node_instances(conn, node_name)

        ids_to_remove = []

        for i in instance_list:
            if len(ids_to_remove) < num_nodes:
                ids_to_remove.append(i.id)
            else:
                break

        actual_num_to_remove = len(ids_to_remove)
        if actual_num_to_remove == 0:
            self._logger.info('No nodes to remove')
            return 0
        elif actual_num_to_remove < num_nodes:
            self._logger.info('Actual number of nodes of type "{0}" is {1}'.format(node_name, actual_num_to_remove))


        self._logger.info('Removing {0} nodes of type "{1}"...'.format(actual_num_to_remove, node_name))

        success = self._terminate_instances_and_wait(conn, ids_to_remove)

        if success:
            return actual_num_to_remove
        else:
            return -1


    def _delete_cluster_info(self):
        files = [defaults.cluster_info_file, defaults.current_controller_ip_file,
                 defaults.cached_cluster_file_path, defaults.cached_environment_file_path]
        for f in files:
            full = os.path.expanduser(f)
            if os.path.isfile(full):
                os.remove(full)

        dirs = [defaults.local_session_data_dir, defaults.local_environment_dir]
        for d in dirs:
            full = os.path.expanduser(d)
            if os.path.exists(full):
                shutil.rmtree(full)

        return True

    def _terminate_instances_and_wait(self, conn, instance_ids):
        num_instances = len(instance_ids)
        conn.terminate_instances(instance_ids=instance_ids)
        def instances_terminated():
            term_filter = {'instance-state-name': 'terminated'}
            num_terminated = len(conn.get_only_instances(instance_ids=instance_ids, filters=term_filter))
            return num_terminated == num_instances

        success = retry_till_true(instances_terminated, 2)
        if not success:
            self._logger.error('Timeout while trying to terminate instances in {0}'.format(self.cluster_name))
            return False
        else:
            self._logger.debug('{0} instances terminated'.format(num_instances))

        return True

    def terminate_cluster(self, leave_shared_volume, force_delete_shared_volume):
        conn = boto.ec2.connect_to_region(self._config['region'],
                    aws_access_key_id=self._config['access_key_id'],
                    aws_secret_access_key=self._config['secret_access_key'])

        if not conn:
            raise ClusterException('Cannot connect to AWS')

        instance_list = self._get_instances(self.cluster_name, connection=conn)
        num_instances = len(instance_list)
        instances = [ i.id for i in instance_list ]

        if not instances:
            self._logger.info('Nothing to terminate. Cleaning up.')
            self._delete_cluster_info()
            return True

        self._logger.info('Terminating {0} instances'.format(num_instances))

        self._terminate_instances_and_wait(conn, instances)

        # Shared volume
        volumes = conn.get_all_volumes(filters={'tag:Attached':self.cluster_name})
        byo_volume = True if volumes else False
        if byo_volume:
            shared_volume = volumes[0]
            shared_volume.remove_tags({'Attached': self.cluster_name})
        else:
            volumes = conn.get_all_volumes(filters={'tag:{0}'.format(defaults.instance_tag_key):self.cluster_name})
            shared_volume = volumes[0]
        
        if leave_shared_volume:
            self._logger.info('Shared volume "{0}" has not been deleted'.format(shared_volume.id))
        else:
            if force_delete_shared_volume or not byo_volume:
                if shared_volume.delete():
                    self._logger.info('Shared volume "{0}" has been deleted'.format(shared_volume.id))
                else:
                    self._logger.error('Unable to delete volume in {0}: {1}'.format(self.cluster_name, shared_volume.id))
            else:
                self._logger.info('Shared volume "{0}" has not been deleted'.format(shared_volume.id))
            
        # Delete security group
        sg = conn.get_all_security_groups(filters={'tag:{0}'.format(defaults.instance_tag_key):self.cluster_name})
        sg_deleted = [ g.delete() for g in sg ]
        if False in sg_deleted:
            self._logger.error('Unable to delete security group for {0}'.format(self.cluster_name))
        else:
            self._logger.debug('Deleted security group')

        # Delete cluster info
        self._delete_cluster_info()

        return True


    def docker_build_image(self, full_path, image_name):
        """
        Create a new docker image
        """

        vars_dict = {
                'cluster_name': self.cluster_name,
                'dockerfile_path': os.path.dirname(full_path),
                'dockerfile_folder': os.path.basename(full_path),
                'image_name': image_name,
                }

        if not os.path.isdir(full_path):
            self._logger.error("Folder '{0}' does not exist".format(full_path))
            return False

        if not os.path.exists("{0}/Dockerfile".format(full_path)):
            self._logger.error("Folder '{0}' does not have a Dockerfile".format(full_path))
            return False

        vars_file = self._make_vars_file(vars_dict)
        self._logger.info('Started building docker image {0}'.format(image_name))
        AnsibleHelper.run_playbook(defaults.get_script('ansible/docker_01_build_image.yml'),
                                   vars_file.name,
                                   self._config['key_file'],
                                   env=self._ansible_env_credentials(),
                                   hosts_file=os.path.expanduser(defaults.current_controller_ip_file))
        vars_file.close()
        self._logger.info('Finished building docker image')
        return True

    def docker_image_info(self, image_name_str):
        """
        Gets information of a Docker image
        """
        if ':' in image_name_str:
            image_name, tag_name = image_name_str.split(':', 1)
        else:
            image_name = image_name_str
            tag_name = 'latest'

        image_info = {}
        # TODO: rewrite to use make HTTP calls directly
        with paramiko.SSHClient() as ssh:
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(hostname = self._get_controller_ip(),
                        username = 'root',
                        key_filename = os.path.expanduser(self._config['key_file']))

            # get image_id
            cmd = 'curl registry:5000/v1/repositories/library/{0}/tags/{1}'.format(image_name, tag_name)
            stdin, stdout, stderr = ssh.exec_command(cmd)
            image_id = stdout.read().replace('"','')
            if 'Tag not found' in image_id:
                return None

            # get image_info
            cmd = 'curl registry:5000/v1/images/{0}/json'.format(image_id)
            stdin, stdout, stderr = ssh.exec_command(cmd)
            json_results = json.loads(stdout.read())
            image_info = { 'image_name': image_name,
                           'tag_name': tag_name,
                           'image_id': image_id,
                           'author': json_results.get('author',''),
                           'created': json_results.get('created','')
                           }
        return image_info

    def sync_put(self, local_path, remote_path):
        """
        Sync local folder to the cluster
        """
        # Check local path
        src_path = os.path.abspath(local_path)
        if not os.path.isdir(src_path):
            message = "Folder '{0}' does not exist".format(src_path)
            return (False, message)

        dst_path = '/home/data/{0}'.format(remote_path)
        vars_dict={
                'src_path': src_path,
                'dst_path': dst_path,
                }
        vars_file = self._make_vars_file(vars_dict)
        self._logger.debug('Started sync folder')
        AnsibleHelper.run_playbook(defaults.get_script('ansible/file_01_sync_put.yml'),
                                   vars_file.name,
                                   self._config['key_file'],
                                   env=self._ansible_env_credentials(),
                                   hosts_file=os.path.expanduser(defaults.current_controller_ip_file))
        vars_file.close()
        self._logger.debug('Finished sync folder')
        return (True, 'Ok')


    def sync_get(self, local_path, remote_path):
        """
        Sync folder from the cluster to local
        """
        # Check local path
        dst_path = os.path.abspath(local_path)
        if not os.path.isdir(dst_path):
            message = "Folder '{0}' does not exist".format(dst_path)
            return (False, message)

        # Check remote path
        remote_path = '/home/data/{0}'.format(remote_path)
        with paramiko.SSHClient() as ssh:
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(hostname = self._get_controller_ip(), username = 'root',
                        key_filename = os.path.expanduser(self._config['key_file']))

            # check if folder exists
            cmd = "ls -d '{0}'".format(remote_path)
            stdin, stdout, stderr = ssh.exec_command(cmd)
            output_content = stdout.read()
            if 'cannot access' in stderr.read():
                message = "Error: Folder '{0}' does not exists.".format(remote_path)
                return (False, message)

        src_path = remote_path
        vars_dict={
                'src_path': src_path,
                'dst_path': dst_path,
                }
        vars_file = self._make_vars_file(vars_dict)
        self._logger.debug('Started sync folder')
        AnsibleHelper.run_playbook(defaults.get_script('ansible/file_02_sync_get.yml'),
                                   vars_file.name,
                                   self._config['key_file'],
                                   env=self._ansible_env_credentials(),
                                   hosts_file=os.path.expanduser(defaults.current_controller_ip_file))
        vars_file.close()
        self._logger.debug('Finished sync folder')
        return (True, 'Ok')

    def ls(self, remote_path):
        """
        List content of a folder on the on cluster
        """
        with paramiko.SSHClient() as ssh:
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(hostname = self._get_controller_ip(), username = 'root',
                        key_filename = os.path.expanduser(self._config['key_file']))

            remote_path = '/home/data/{0}'.format(remote_path)
            cmd = "ls -al '{0}'".format(remote_path)
            stdin, stdout, stderr = ssh.exec_command(cmd)
            output_content = stdout.read()
            if 'cannot access' in stderr.read():
                message = "Error: Folder '{0}' does not exists.".format(remote_path)
                return (False, message)

            return (True, output_content)


    def rm(self, remote_path):
        """
        Delete content of a folder on the on cluster
        """
        with paramiko.SSHClient() as ssh:
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(hostname = self._get_controller_ip(), username = 'root',
                        key_filename = os.path.expanduser(self._config['key_file']))

            # check if folder exists
            remote_path = '/home/data/{0}'.format(remote_path)
            cmd = "ls -d '{0}'".format(remote_path)
            stdin, stdout, stderr = ssh.exec_command(cmd)
            output_content = stdout.read()
            if 'cannot access' in stderr.read():
                message = "Error: Folder '{0}' does not exists.".format(remote_path)
                return (False, message)

            cmd = "rm -fr '{0}'".format(remote_path)
            stdin, stdout, stderr = ssh.exec_command(cmd)
            output_content = stdout.read()
            # TODO: More error checking may need to be added
            if 'cannot access' in stderr.read():
                message = "Error: Failed to delete folder '{0}'.".format(remote_path)
                return (False, message)

            return (True, 'Ok')


    def workon(self):
        """
        Sets a working cluster
        """
        # Getting cluster info
        instances = self._get_instances(self.cluster_name)
        controller_ip = None
        cluster_name = None
        for instance in instances:
            if defaults.controller_name_format.format(self.cluster_name) in instance.tags['Name']:
                controller_ip = instance.ip_address
                cluster_name = self.cluster_name

        if not controller_ip:
            return False

        self._create_config_dirs()
        # Write controller_ip
        self._set_cluster_info({'controller_ip': controller_ip, 'cluster_name': cluster_name})
        ip_file = os.path.expanduser(defaults.current_controller_ip_file)
        self._write_to_hosts_file(ip_file, [controller_ip], 'controller', overwrite=True)

        # Sync from controller
        self._copy_environment_from_controller()

        return True


    def get_cluster_info(self):
        """
        Gets information about instances running in current cluster,
        returns dictionary
        """
        nodes_info = {}
        controller_info = {}
        central_logging_info = {}
        instances = self._get_instances(self.cluster_name)

        for instance in instances:
            node_name = instance.tags[defaults.instance_node_type_tag_key]
            if node_name == defaults.controller_name_tag_value:
                # Controller instance
                if controller_info:     # Shouldn't happen
                    self._logger.warning('There appears to be more than one controller running')

                launch_time = parser.parse(instance.launch_time)
                uptime = (datetime.now(launch_time.tzinfo) - launch_time).total_seconds()
                controller_info = {
                                    'ip': str(instance.ip_address),
                                    'type': instance.instance_type,
                                    'uptime': int(uptime)
                }
            elif node_name == defaults.central_logging_name_tag_value:
                if central_logging_info:     # Shouldn't happen
                    self._logger.warning('There appears to be more than one central logging instance running')

                central_logging_info = {
                                    'type': instance.instance_type
                }
            else:
                if node_name not in nodes_info:
                    nodes_info[node_name] = {
                                        'type': instance.instance_type,
                                        'count': 1
                    }
                else:
                    nodes_info[node_name]['count'] += 1

        info = {
                'cluster_name': self.cluster_name,
                'instance_count': len(instances),
                'nodes': nodes_info,
                'controller': controller_info,
                'central_logging': central_logging_info
        }

        return info

    def get_shared_volume_usage_info(self):
        """
        Gets information about the free space on the shared volume,
        returns dictionary
        """
        info = {}
        ssh = self._ssh_to_controller()

        cmd = 'df -h | grep {0}'.format(defaults.shared_volume_path[:-1])
        stdin, stdout, stderr = ssh.exec_command(cmd)

        volume_info = ' '.join(stdout.read().split()).split()
        if volume_info:
            info =  { 'total': volume_info[1],
                      'used': volume_info[2],
                      'used_percent': volume_info[4],
                      'free': volume_info[3]
                    }
        return info


    def connect_to_container(self, component_name):
        '''
        Connects to a docker container and gets an interactive shell
        '''
        key_file_local = os.path.expanduser(self._config['key_file'])
        key_file_remote = '/root/{0}/{1}'.format(defaults.remote_host_scripts_dir, defaults.remote_host_key_file)
        container_id_script_local = defaults.get_script(defaults.container_id_script_file)
        container_id_script_remote = '/root/{0}/{1}'.format(defaults.remote_host_scripts_dir,defaults.container_id_script_file)
        container_id_script_node = '/tmp/{0}'.format(defaults.container_id_script_file)
        node = '{0}.marathon.mesos'.format(component_name)

        # SSH controller
        with self._ssh_to_controller() as ssh:
            self._logger.info("Connecting to '{0}' component".format(component_name))
            # Copy files to controller
            sftp = ssh.open_sftp()
            sftp.put(key_file_local, key_file_remote)
            sftp.put(container_id_script_local, container_id_script_remote)
            sftp.chmod(key_file_remote, stat.S_IRUSR | stat.S_IWUSR)
            sftp.close()

            def _retry(cmd):
                retry = 0
                while retry < 3:
                    stdin, stdout, stderr = ssh.exec_command(cmd)
                    if not stderr.readlines():
                        break
                    retry += 1
                    self._logger.info('Retry: {0}'.format(retry))
                    time.sleep(3)
                return (retry <3 ), stdout

            # Copy script to node
            cmd='scp -i {0} -oStrictHostKeyChecking=no {1} {2}:{3}'.format(key_file_remote,
                                                                           container_id_script_remote, node, container_id_script_node)
            success, stdout = _retry(cmd)
            if not success:
                self._logger.debug("Failed to copy scripts to controller")
                message = "Failed to connect to '{0}' component, try later".format(component_name)
                return (False, message)

            # Get container id
            cmd='ssh -i {0} -oStrictHostKeyChecking=no {1} source {2} {3}'.format(key_file_remote,
                                                                                  node, container_id_script_node, component_name)
            success, stdout = _retry(cmd)
            if not success:
                self._logger.debug("Failed to get container id for '{0}' component".format(component_name))
                message = "Failed to connect to '{0}' component, try later".format(component_name)
                return (False, message)

            container_id = stdout.readline().replace('\n','')

        # Shell
        node = '{0}.marathon.mesos'.format(component_name)
        cmd='ssh -i {0} -oStrictHostKeyChecking=no -A -t root@{1} \
             ssh -i {2} -oStrictHostKeyChecking=no -A -t {3} \
             docker exec -ti {4} bash'.format(key_file_local, self._get_controller_ip(),
                         key_file_remote, node, container_id)
        os.system(cmd)

        # Remove keys
        with self._ssh_to_controller() as ssh:
            cmd='rm -fr {0}'.format(key_file_remote)
            success, stdout = _retry(cmd)
            if not success:
                message = 'Failed to remove keys from controller'
                self._logger.debug(message)
                return (False, message)

        return (True, 'Ok')

    def connect_to_central_logging(self):
        """
        Creates an SSH tunnel to the logging system
        """
        if not self.get_central_logging_ip():
            message = 'No logging system has been set'
            return (True, message)

        central_logging_port = defaults.central_logging_port
        self.make_tunnel_on_controller(central_logging_port, self.get_central_logging_ip(), central_logging_port)
        success = self.create_permanent_tunnel_to_controller(central_logging_port, central_logging_port)

        if not success:
            message = 'Failed create tunnel to centralized logging system'
            self._logger.debug(message)
            return (False, message)

        message = 'The logging system is available at this URL:\nhttp://localhost:{0}'.format(central_logging_port)
        return (True, message)

    def ls_volumes(self):
        conn = boto.ec2.connect_to_region(self._config['region'],
                    aws_access_key_id=self._config['access_key_id'],
                    aws_secret_access_key=self._config['secret_access_key'])
        volumes = conn.get_all_volumes(filters={'tag-key':defaults.instance_tag_key})
        shared_volumes = []
        for v in volumes:
            if v.status == 'available':
                utc = datetime.strptime(v.create_time, '%Y-%m-%dT%H:%M:%S.%fZ').replace(tzinfo=tz.tzutc())
                shared_volumes.append({'id': v.id, 'created_ts': utc.astimezone(tz.tzlocal()).strftime("%Y-%m-%d %H:%M:%S"), 
                                       'size':v.size, 'cluster_name':v.tags.get(defaults.instance_tag_key,'')})
        return shared_volumes

    def rm_volume(self, volume_id):
        """
        Deletes a shared volume left on cluster termination
        """
        success = False
        message = ''
        conn = boto.ec2.connect_to_region(self._config['region'],
                    aws_access_key_id=self._config['access_key_id'],
                    aws_secret_access_key=self._config['secret_access_key'])
        try:
            volume_obj = conn.get_all_volumes([volume_id])[0]
            if volume_obj.status == 'available':
                if defaults.instance_tag_key in volume_obj.tags:
                    if conn.delete_volume(volume_id):
                        success = True
                        message = 'Volume "{0}" has been deleted'.format(volume_id)
                    else:
                        message = 'Unable to delete volume "{0}"'.format(volume_id)
                else:
                    message = 'Volume "{0}" was not created by Clusterous'.format(volume_id)
            else:
                message = 'Volume "{0}" cannot be deleted because it is currently in use'.format(volume_id)
        except boto.exception.EC2ResponseError as e:
            message = 'Volume "{0}" does not exist'.format(volume_id)
        return (success, message)
