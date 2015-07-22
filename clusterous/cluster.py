import subprocess
import tempfile
import sys
import os
import yaml
import logging
import time
import shutil
import json
import stat
from datetime import datetime
from dateutil import parser
from dateutil.relativedelta import relativedelta

import boto.ec2
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
        if cluster_name_required:
            if cluster_name is None:
                cluster_name = self._get_working_cluster_name()
                if cluster_name is None:
                    message = 'No working cluster has been set.'
                    self._logger.error(message)
                    raise NoWorkingClusterException(message)
            self.cluster_name = cluster_name

    def _get_working_cluster_name(self):
        cluster_info_file = os.path.expanduser(defaults.CLUSTER_INFO_FILE)
        if not os.path.isfile(cluster_info_file):
            return None

        with open(os.path.expanduser(cluster_info_file), 'r') as stream:
            cluster_info = yaml.load(stream)

        return cluster_info.get('cluster_name')


    def _get_controller_ip(self):
        ip = None
        ip_file = os.path.expanduser(defaults.current_controller_ip_file)
        if os.path.isfile(ip_file):
            f = open(ip_file, 'r')
            ip = f.read().strip()
            f.close
        else:
            raise ValueError('Cannot find controller IP: {0}'.format(ip_file))
        return ip

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

    def _ec2_vars_dict(self):
        return {
                'AWS_KEY': self._config['access_key_id'],
                'AWS_SECRET': self._config['secret_access_key'],
                'region': self._config['region'],
                'keypair': self._config['key_pair'],
                'vpc_id': self._config['vpc_id'],
                'vpc_subnet_id': self._config['subnet_id'],
                'cluster_name': self.cluster_name,
                'security_group_name': defaults.security_group_name_format.format(self.cluster_name),
                'controller_ami_id': defaults.controller_ami_id,
                'controller_instance_name': defaults.controller_name_format.format(self.cluster_name),
                'controller_instance_type': defaults.controller_instance_type,
                'node_name': defaults.node_name_format.format(self.cluster_name),
                'node_ami_id': defaults.node_ami_id,
                'clusterous_s3_bucket': self._config['clusterous_s3_bucket'],
                'registry_s3_path': defaults.registry_s3_path,
                'current_controller_ip_file': defaults.current_controller_ip_file,
                'remote_scripts_dir': defaults.get_remote_dir(),
                'remote_host_scripts_dir': defaults.remote_host_scripts_dir
                }

    def _ansible_env_credentials(self):
        return {
                'AWS_ACCESS_KEY_ID': self._config['access_key_id'],
                'AWS_SECRET_ACCESS_KEY': self._config['secret_access_key']
                }

    def _run_remote_vars_dict(self):
        return {
                'controller_ip': self._get_controller_ip(),
                'key_file_src': self._config['key_file'],
                'key_file_name': defaults.remote_host_key_file,
                'vars_file_src': None,  # must be filled in
                'vars_file_name': defaults.remote_host_vars_file,
                'remote_dir': defaults.remote_host_scripts_dir,
                'playbook_file': None
                }

    def _make_vars_file(self, vars_dict):
        vars_file = tempfile.NamedTemporaryFile()
        vars_file.write(yaml.dump(vars_dict, default_flow_style=False))
        vars_file.flush()
        return vars_file

    def _run_remote(self, vars_dict, playbook):

        vars_file = self._make_vars_file(vars_dict)

        local_vars = self._run_remote_vars_dict()
        local_vars['vars_file_src'] = vars_file.name
        local_vars['playbook_file'] = playbook

        local_vars_file = self._make_vars_file(local_vars)

        AnsibleHelper.run_playbook(get_script('ansible/run_remote.yml'),
                      local_vars_file.name, self._config['key_file'],
                      hosts_file=os.path.expanduser(defaults.current_controller_ip_file))

        local_vars_file.close()
        vars_file.close()

    def _get_instances(self, cluster_name):
        conn = boto.ec2.connect_to_region(self._config['region'],
                    aws_access_key_id=self._config['access_key_id'],
                    aws_secret_access_key=self._config['secret_access_key'])

        # Delete instances
        instance_filters = { 'tag:Name':
                        ['{0}_controller'.format(cluster_name),
                        '{0}_node'.format(cluster_name)],
                        'instance-state-name': ['running', 'pending']
                        }
        instance_list = conn.get_only_instances(filters=instance_filters)
        return instance_list

    def _ssh_to_controller(self):
        try:
            ssh = paramiko.SSHClient()
            ssh.load_system_host_keys()
            ssh.connect(hostname = self._get_controller_ip(),
                        username = 'root',
                        key_filename = os.path.expanduser(self._config['key_file']))
        except paramiko.AuthenticationException as e:
            self._logger.error('Could not connect to controller')
            raise e

        return ssh


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

    def create_permanent_tunnel_to_controller(self, remote_port, local_port):
        """
        Creates a persistent  SSH tunnel from local machine to controller by running
        the ssh command in the background
        """

        key_file = os.path.expanduser(self._config['key_file'])

        # Temporary file containing ssh socket data
        ssh_sock_file = '{0}/clusterous_tunnel_%h_{1}.sock'.format(
                        os.path.expanduser(defaults.local_session_data_dir), local_port)

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

    def init_cluster(self, cluster_name):
        """
        Initialise security group(s), cluster controller etc
        """
        self.cluster_name = cluster_name

        # Create dirs
        for directory in [defaults.local_config_dir, defaults.local_session_data_dir]:
            d = os.path.expanduser(directory)
            if not os.path.exists(d):
                os.makedirs(d)

        vars_dict = self._ec2_vars_dict()

        vars_file = self._make_vars_file(vars_dict)

        # Run ansible

        env = self._ansible_env_credentials()
        self._logger.debug('Creating security group')
        AnsibleHelper.run_playbook(get_script('ansible/init_01_create_sg.yml'),
                                   vars_file.name, self._config['key_file'],
                                   env=env)

        self._logger.debug('Ensuring Docker registry bucket exists')
        AnsibleHelper.run_playbook(get_script('ansible/init_02_create_s3_bucket.yml'),
                                   vars_file.name, self._config['key_file'],
                                   env=env)

        self._logger.debug('Creating and configuring controller instance...')
        AnsibleHelper.run_playbook(get_script('ansible/init_03_create_controller.yml'),
                                   vars_file.name, self._config['key_file'],
                                   env=env)
        self._logger.debug('Launched controller instance at {0}'.format(self._get_controller_ip()))

        # TODO: this is useful for debugging, but remove at a later stage
        self.create_permanent_tunnel_to_controller(8080, 8080)

        # Set working cluster
        self.workon()

        vars_file.close()


    def launch_nodes(self, num_nodes, instance_type, node_tag):
        """
        Launch a group of application nodes of the same type.
        node_name is the Mesos tag by which the application can find a node
        """
        vars_dict = self._ec2_vars_dict()
        vars_dict['num_nodes'] = num_nodes
        vars_dict['instance_type'] = instance_type
        vars_dict['node_tag'] = node_tag

        self._logger.debug('Adding {0} nodes named "{1}" to cluster...'.format(num_nodes, node_tag))
        self._run_remote(vars_dict, 'create_nodes.yml')


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
            ssh.load_system_host_keys()
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
        self._logger.info('Started sync folder')
        AnsibleHelper.run_playbook(defaults.get_script('ansible/file_01_sync_put.yml'),
                                   vars_file.name,
                                   self._config['key_file'],
                                   env=self._ansible_env_credentials(),
                                   hosts_file=os.path.expanduser(defaults.current_controller_ip_file))
        vars_file.close()
        self._logger.info('Finished sync folder')
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
            ssh.load_system_host_keys()
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
        self._logger.info('Started sync folder')
        AnsibleHelper.run_playbook(defaults.get_script('ansible/file_02_sync_get.yml'),
                                   vars_file.name,
                                   self._config['key_file'],
                                   env=self._ansible_env_credentials(),
                                   hosts_file=os.path.expanduser(defaults.current_controller_ip_file))
        vars_file.close()
        self._logger.info('Finished sync folder')
        return (True, 'Ok')

    def ls(self, remote_path):
        """
        List content of a folder on the on cluster
        """
        with paramiko.SSHClient() as ssh:
            ssh.load_system_host_keys()
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
            ssh.load_system_host_keys()
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
        data = {}
        for instance in instances:
            if defaults.controller_name_format.format(self.cluster_name) in instance.tags['Name']:
                data['controller']={'ip': str(instance.ip_address)}
                data['cluster_name']=self.cluster_name

        if not data:
            return (False, 'Cluster "{0}" does not exist'.format(self.cluster_name))

        # Write cluster_info
        cluster_info_file = os.path.expanduser(defaults.CLUSTER_INFO_FILE)
        with open(cluster_info_file,'w+') as fw:
            fw.write(yaml.dump(data, default_flow_style=False))

        # Write controller_ip
        ip_file = os.path.expanduser(defaults.current_controller_ip_file)
        with open(ip_file,'w+') as fw:
            fw.write(data.get('controller',{}).get('ip'))

        return (True, 'Ok')

    def info_status(self):
        info = {'name': self._get_working_cluster_name(),
                'up_time': '',
                'controller_ip': '',
                }
        instances = self._get_instances(self.cluster_name)
        for instance in instances:
            if defaults.controller_name_format.format(self.cluster_name) in instance.tags['Name']:
                info['controller_ip'] = str(instance.ip_address)
                launch_time = parser.parse(instance.launch_time)
                info['up_time'] = relativedelta(datetime.now(launch_time.tzinfo), launch_time)
        return info

    def info_instances(self):
        info = {}
        instances = self._get_instances(self.cluster_name)
        for instance in instances:
            if instance.instance_type not in info:
                info[instance.instance_type] = 0
            info[instance.instance_type] += 1
        return info

    def info_shared_volume(self):
        info = {'total': '',
                'used': '',
                'used_pct': '',
                'free': ''}
        with paramiko.SSHClient() as ssh:
            ssh.load_system_host_keys()
            ssh.connect(hostname = self._get_controller_ip(),
                        username = 'root',
                        key_filename = os.path.expanduser(self._config['key_file']))
            cmd = 'df -h |grep {0}'.format(defaults.shared_volume_path[:-1])
            stdin, stdout, stderr = ssh.exec_command(cmd)
            volume_info = ' '.join(stdout.read().split()).split()
            if volume_info:
                info['total'] = volume_info[1]
                info['used'] =  volume_info[2]
                info['used_pct'] = volume_info[4]
                info['free'] = volume_info[3]
        return info

    def terminate_cluster(self):
        conn = boto.ec2.connect_to_region(self._config['region'],
                    aws_access_key_id=self._config['access_key_id'],
                    aws_secret_access_key=self._config['secret_access_key'])
        instance_list = self._get_instances(self.cluster_name)
        num_instances = len(instance_list)
        instances = [ i.id for i in instance_list ]

        self._logger.info('Terminating {0} instances'.format(num_instances))
        conn.terminate_instances(instance_ids=instances)

        def instances_terminated():
            term_filter = {'instance-state-name': 'terminated'}
            num_terminated = len(conn.get_only_instances(instance_ids=instances, filters=term_filter))
            return num_terminated == num_instances

        success = retry_till_true(instances_terminated, 2)
        if not success:
            self._logger.error('Timeout while trying to terminate instances in {0}'.format(self.cluster_name))
        else:
            self._logger.debug('{0} instances terminated'.format(num_instances))

        # Delete EBS volume
        volumes = conn.get_all_volumes(filters={'tag:Name':self.cluster_name})
        volumes_deleted = [ v.delete() for v in volumes ]
        volume_ids_str = ','.join([ v.id for v in volumes])
        if False in volumes_deleted:
            self._logger.error('Unable to delete volume in {0}: {1}'.format(self.cluster_name, volume_ids_str))
        else:
            self._logger.debug('Deleted shared volume: {0}'.format(volume_ids_str))

        # Delete security group
        sg = conn.get_all_security_groups(filters={'tag:Name':'{0}-sg'.format(self.cluster_name)})
        sg_deleted = [ g.delete() for g in sg ]
        if False in sg_deleted:
            self._logger.error('Unable to delete security group for {0}'.format(self.cluster_name))
        else:
            self._logger.debug('Deleted security group')

        # Delete cluster info
        os.remove(os.path.expanduser(defaults.CLUSTER_INFO_FILE))
        os.remove(os.path.expanduser(defaults.current_controller_ip_file))
        shutil.rmtree(os.path.expanduser(defaults.local_session_data_dir))

        return True
