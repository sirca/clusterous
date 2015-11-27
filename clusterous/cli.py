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

import sys
import os
import defaults
import argparse
import logging
import textwrap

import tabulate
from dateutil import relativedelta

import clusterousmain
from clusterous import __version__, __prog_name__
from helpers import NoWorkingClusterException

class CLIParser(object):
    """
    Clusterous Command Line Interface
    """

    def __init__(self):
        pass

    def _configure_logging(self, level='INFO'):
        logging_dict = {
                            'version': 1,
                            'disable_existing_loggers': False,
                            'formatters': {
                                'standard': {
                                    'format': '%(message)s'
                                },
                            },
                            'handlers': {
                                'default': {
                                    'level': level,
                                    'class':'logging.StreamHandler',
                                },
                            },
                            'loggers': {
                                '': {
                                    'handlers': ['default'],
                                    'level': level,
                                    'propagate': True
                                },
                            }
                        }

        logging.config.dictConfig(logging_dict)

        # Disable logging for various libraries
        # TODO: is it possible to do this in a simpler way?
        libs = ['boto', 'paramiko', 'requests', 'marathon']
        for l in libs:
            logging.getLogger(l).setLevel(logging.WARNING)

    @staticmethod
    def boldify(s):
        """
        Adds shell formatting characters to s to make it bold when printed
        """
        return '\033[1m' + str(s) + '\033[0m'


    def _create_args(self, parser):
        parser.add_argument('--verbose', '-v', dest='verbose', action='store_true',
            default=False, help='Print verbose debug output')
        parser.add_argument('--version', action='version', version='%(prog)s {0}'.format(__version__))

    def _create_subparsers(self, parser):
        subparser = parser.add_subparsers(description='The following subcommands are available', dest='subcmd')

        # Create new cluster
        create = subparser.add_parser('create', help='Create a new cluster',
                                        description='Create a new cluster and run any specified environment')
        create.add_argument('--no-run', dest='run', action='store_false', default=True,
                            help='Do not run environment (if specified), just create a bare cluster')
        create.add_argument('profile_file', action='store', help='File containing cluster creation parameters')

        # Status
        cluster_status = subparser.add_parser('status', help='Status of the cluster',
                                                description='Show information on the state of the cluster and any running application')

        # Destroy cluster
        destroy = subparser.add_parser('destroy', help='Destroy the working cluster',
                                            description='Destroy the working cluster, removing all resources')
        destroy.add_argument('--confirm', dest='no_prompt', action='store_true',
            default=False, help='Immediately destroy cluster without prompting for confirmation')
        destroy.add_argument('--leave-shared-volume', dest='leave_shared_volume', action='store_true',
            default=False, help='Do not delete the shared volume')
        destroy.add_argument('--force-delete-shared-volume', dest='force_delete_shared_volume', action='store_true',
            default=False, help='Force deletion of shared volume')

        # Run
        run = subparser.add_parser('run', help='Run an environment from an environment file',
                                        description='Run an environment on the cluster based on the specifications '
                                                    'in an environment file')
        run.add_argument('environment_file', action='store')

        # Quit environment
        quit = subparser.add_parser('quit', help='Stop the running application',
                                        description='Stops the running application containers on the'
                                        ' cluster and removes any SSH tunnels to the application')
        quit.add_argument('--tunnel-only', dest='tunnel_only', action='store_true',
                            default=False, help='Only remove any SSH tunnels, do not stop application')
        quit.add_argument('--confirm', dest='no_prompt', action='store_true', default=False,
                                help='Immediately quit application without prompting for confirmation')


        # workon
        workon = subparser.add_parser('workon', help='Set the working cluster',
                                        description='Set the currently active cluster by name')
        workon.add_argument('cluster_name', action='store', help='Name of the cluster')

        # Connect
        connect = subparser.add_parser('connect', help='Get an interactive shell within a docker container',
                                description='Connects to a docker container and gets an interactive shell')
        connect.add_argument('component_name', action='store', help='Name of the component (see status command)')


        # Sync: put
        sync_put = subparser.add_parser('put', help='Copy a folder from local to the cluster')
        sync_put.add_argument('local_path', action='store', help='Path to the local folder')
        sync_put.add_argument('remote_path', action='store', help='Path on the shared volume', nargs='?', default='')

        # Sync: get
        sync_get = subparser.add_parser('get', help='Copy a folder from cluster to local')
        sync_get.add_argument('remote_path', action='store', help='Path on the shared volume')
        sync_get.add_argument('local_path', action='store', help='Path to the local folder')

        # ls
        ls = subparser.add_parser('ls', help='List contents of the shared volume')
        ls.add_argument('remote_path', action='store', help='Path on the shared volume', nargs='?', default='')

        # rm
        rm = subparser.add_parser('rm', help='Delete a folder on the shared volume')
        rm.add_argument('remote_path', action='store', help='Path on the shared volume')

        # add-nodes
        add_nodes = subparser.add_parser('add-nodes', help='Add nodes to the running cluster')
        add_nodes.add_argument('num_nodes', action='store', help='Number of nodes to add', type=int)
        add_nodes.add_argument('node_name', action='store', help='Name of node type to add', default=None, nargs='?')

        # rm-nodes
        rm_nodes = subparser.add_parser('rm-nodes', help='Remove nodes from the running cluster')
        rm_nodes.add_argument('num_nodes', action='store', help='Number of nodes to remove', type=int)
        rm_nodes.add_argument('node_name', action='store', help='Name of node type to remove', default=None, nargs='?')

        # Build Docker image
        build = subparser.add_parser('build-image', help='Build a new Docker image',
                                        description='Build a Docker image on the cluster from a Dockerfile')
        build.add_argument('dockerfile_folder', action='store', help='Local folder name which contains the Dockerfile')
        build.add_argument('image_name', action='store', help='Name of the docker image to be created on the cluster')

        # Docker image info
        image_info = subparser.add_parser('image-info', help='Get information on a Docker image',
                                            description='Get information about a Docker image on the cluster')
        image_info.add_argument('image_name', action='store', help='Name of the docker image available on the cluster')

        # Central logging
        central_logging = subparser.add_parser('logging', help='Creates an SSH tunnel to the logging system',
                                                description='Creates an SSH tunnel to the centralized logging system and presents the URL to access it')

        # ls-volumes
        ls_volumes = subparser.add_parser('ls-volumes', help='List unattached shared volumes',
                                          description='List unattached shared volumes left from previously destroyed clusters')

        # rm-shared
        workon = subparser.add_parser('rm-volume', help='Delete unattached shared volume',
                                          description='Deletes unattached shared volume left from previously destroyed clusters')
        workon.add_argument('volume_id', action='store', help='Volume ID')



    def _init_clusterous_object(self, args):
        app = None

        if args.verbose:
            self._configure_logging('DEBUG')
        else:
            self._configure_logging('INFO')

        try:
            app = clusterousmain.Clusterous()
        except clusterousmain.ConfigError as e:
            print >> sys.stderr, 'Error in Clusterous configuration file', e.filename
            print >> sys.stderr, e
            sys.exit(-1)
        return app

    def _workon(self, args):
        app = self._init_clusterous_object(args)
        success, message = app.workon(cluster_name = args.cluster_name)
        print message

        return 0 if success else 1

    def _destroy_cluster(self, args):
        if args.leave_shared_volume and args.force_delete_shared_volume:
            print 'Error: Use --leave-shared-volume or --force-delete-shared-volume but not both at the same time'
            return 1

        app = self._init_clusterous_object(args)
        cl = app.make_cluster_object()
        if not args.no_prompt:
            prompt_str = 'This will destroy the cluster {0}. All data on the cluster will be deleted. Continue (y/n)? '.format(cl.cluster_name)
            cont = raw_input(prompt_str)
            if cont.lower() != 'y' and cont.lower() != 'yes':
                print 'Doing nothing'
                return 1

        app = self._init_clusterous_object(args)
        app.destroy_cluster(args.leave_shared_volume, args.force_delete_shared_volume)
        return 0

    def _create_cluster(self, args):
        app = self._init_clusterous_object(args)
        success = False

        try:
            success, message = app.create_cluster(args.profile_file, args.run)
            if success and message:
                print '\nMessage for user:'
                print message
        except clusterousmain.ProfileError as e:
            print >> sys.stderr, 'Error in profile file {0}:'.format(args.profile_file)
            print >> sys.stderr, e.message
        except clusterousmain.EnvironmentFileError as e:
            print >> sys.stderr, 'Error in environment file {0}'.format(e.filename)
            print >> sys.stderr, e.message

        return 0 if success else 1

    def _run_environment(self, args):
        app = self._init_clusterous_object(args)
        success = False

        try:
            success, message = app.run_environment(args.environment_file)
        except clusterousmain.EnvironmentFileError as e:
            print >> sys.stderr, 'Error in environment file {0}'.format(e.filename)
            print >> sys.stderr, e.message

        if success and message:
            print '\nMessage for user:'
            print message

        return 0 if success else 1

    def _docker_image_info(self, args):
        app = self._init_clusterous_object(args)
        info = app.docker_image_info(args.image_name)
        if not info:
            print 'Docker image "{0}" does not exist in the Docker registry'.format(args.image_name)
            return 1
        else:
            print 'Docker image: {}:{}\nImage id: {}\nAuthor: {}\nCreated: {}'.format(
                info['image_name'], info['tag_name'], info['image_id'], info['author'], info['created'])
            return 0

    def _sync_put(self, args):
        app = self._init_clusterous_object(args)
        success, message = app.sync_put(local_path = args.local_path,
                                        remote_path = args.remote_path)
        if not success:
            print message
            return 1
        return 0

    def _sync_get(self, args):
        app = self._init_clusterous_object(args)
        success, message = app.sync_get(remote_path = args.remote_path,
                                        local_path = args.local_path)
        if not success:
            print message
            return 1
        return 0

    def _ls(self, args):
        app = self._init_clusterous_object(args)
        success, message = app.ls(remote_path = args.remote_path)
        print message
        return 0 if success else 1

    def _rm(self, args):
        app = self._init_clusterous_object(args)
        success, message = app.rm(remote_path = args.remote_path)
        print message
        return 0 if success else 1

    def _scale_nodes(self, args, action):
        if not action in ['add', 'rm']:
            raise ValueError('action must be "add" or "rm"')

        if args.num_nodes < 1:
            print >> sys.stderr, 'num_nodes must be at least 1'
            return False

        app = self._init_clusterous_object(args)
        success = False
        if action in ('add', 'rm'):
            success, message = app.scale_nodes(action, args.num_nodes, args.node_name)

        if not success:
            print >> sys.stderr, message

        return success


    def _connect_to_container(self, args):
        app = self._init_clusterous_object(args)
        success, message = app.connect_to_container(component_name = args.component_name)
        if not success:
            print message
            return 1
        return 0

    def _central_logging(self, args):
        app = self._init_clusterous_object(args)
        success, message = app.central_logging()
        print message
        return 0 if success else 1

    def _cluster_status(self, args):
        app = self._init_clusterous_object(args)
        success, info = app.cluster_status()
        if not success:
            print info
            return 1

        # Format cluster info
        central_logging_frag = '' if not info['central_logging'] else ' and central logging'
        instance_plural = '' if info['instance_count'] == 1 else 's'
        print '{0} has {1} instance{2} running, including controller{3}'.format(
                                            self.boldify(info['cluster_name']),
                                            info['instance_count'],
                                            instance_plural,
                                            central_logging_frag)
        # print
        print 'Controller IP:\t{0}'.format(info['controller']['ip'])

        # Calculate uptime
        rd = relativedelta.relativedelta(seconds=info['controller']['uptime'])
        uptime_str = ''
        if rd.days: uptime_str += '{0} days '.format(rd.days)
        if uptime_str or rd.hours: uptime_str += '{0} hours '.format(rd.hours)  # 0 hours is valid if preceeded by "days"
        if rd.minutes: uptime_str += '{0} minutes'.format(rd.minutes)
        print 'Uptime:\t\t{0}'.format(uptime_str)

        # Prepare node information table
        nodes_headers = map(self.boldify, ['Node Name', 'Instance Type', 'Count', 'Running Components'])
        nodes_table = []

        # Add controller and logging instances to table
        nodes_table.append(['[controller]', info['controller']['type'], 1, '--'])

        if info['central_logging']:
            nodes_table.append(['[logging]', info['central_logging']['type'], 1, '--'])

        # Add regular nodes
        for node_name, node_info in info['nodes'].iteritems():
            components_str = '[None]'
            components = []
            for c in node_info['components']:
                components.append(c['name'])
            if components:
                components_str = ', '.join(components)

            line = [node_name, node_info['type'], node_info['count'], components_str]
            nodes_table.append(line)

        # Print table
        print
        print tabulate.tabulate(nodes_table, headers=nodes_headers, tablefmt='plain')

        # Print shared volume info
        if info['shared_volume']:
            print '\n', self.boldify('Shared Volume')
            vinfo = info['shared_volume']
            print '{0} ({1}) used of {2}'.format(vinfo['used'], vinfo['used_percent'], vinfo['total'])
            print '{0} available'.format(vinfo['free'])

        return 0

    def _quit(self, args):
        # If the user specifies --tunnel-only, we don't prompt for confirmation
        if not args.no_prompt and not args.tunnel_only:
            cont = raw_input('This will stop the running cluster application. Continue (y/n)? ')
            if cont.lower() != 'y' and cont.lower() != 'yes':
                print 'Doing nothing'
                return 1

        app = self._init_clusterous_object(args)
        result = app.quit_environment(args.tunnel_only)

        return 0 if result else 1

    def _ls_volumes(self, args):
        app = self._init_clusterous_object(args)
        success, info = app.ls_volumes()

        # Prepare node information table
        headers = map(self.boldify, ['ID', 'Created', 'Size (GB)', 'Last attached to'])
        table = []
        for i in info:
            table.append([i.get('id'), i.get('created_ts'), i.get('size'),i.get('cluster_name')])
        print tabulate.tabulate(table, headers=headers, tablefmt='plain')
        return 0 if success else 1

    def _rm_volume(self, args):
        cont = raw_input('This will delete shared volume "{0}". Continue (y/n)? '.format(args.volume_id))
        if cont.lower() != 'y' and cont.lower() != 'yes':
            print 'Doing nothing'
            return 1

        app = self._init_clusterous_object(args)
        success, message = app.rm_volume(args.volume_id)
        print message
        return 0 if success else 1

    def main(self, argv=None):
        parser = argparse.ArgumentParser(__prog_name__, description='Tool to create and manage compute clusters')

        self._create_args(parser)
        self._create_subparsers(parser)

        args = parser.parse_args(argv)

        status = 0
        try:
            if args.subcmd == 'create':
                status = self._create_cluster(args)
            elif args.subcmd == 'destroy':
                self._destroy_cluster(args)
            elif args.subcmd == 'run':
                self._run_environment(args)
            elif args.subcmd == 'build-image':
                app = self._init_clusterous_object(args)
                app.docker_build_image(args)
            elif args.subcmd == 'image-info':
                app = self._init_clusterous_object(args)
                self._docker_image_info(args)
            elif args.subcmd == 'put':
                status = self._sync_put(args)
            elif args.subcmd == 'get':
                status = self._sync_get(args)
            elif args.subcmd == 'ls':
                status = self._ls(args)
            elif args.subcmd == 'rm':
                status = self._rm(args)
            elif args.subcmd == 'add-nodes':
                status = self._scale_nodes(args, action='add')
            elif args.subcmd == 'rm-nodes':
                status = self._scale_nodes(args, action='rm')
            elif args.subcmd == 'workon':
                status = self._workon(args)
            elif args.subcmd == 'status':
                status = self._cluster_status(args)
            elif args.subcmd == 'connect':
                status = self._connect_to_container(args)
            elif args.subcmd == 'logging':
                status = self._central_logging(args)
            elif args.subcmd == 'quit':
                status = self._quit(args)
            elif args.subcmd == 'ls-volumes':
                status = self._ls_volumes(args)
            elif args.subcmd == 'rm-volume':
                status = self._rm_volume(args)

        # TODO: this exception should not be caught here
        except NoWorkingClusterException as e:
            pass

        return status

def main(argv=None):
    cli = CLIParser()
    return cli.main(argv)
