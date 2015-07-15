import sys
import os
import defaults
import argparse

import clusterous
from helpers import NoWorkingClusterException

class CLIParser(object):
    """
    Clusterous Command Line Interface
    """

    def __init__(self):
        pass

    def _create_args(self, parser):
        parser.add_argument('--verbose', dest='verbose', action='store_true',
            default=False, help='Print verbose debug output')

    def _create_subparsers(self, parser):
        subparser = parser.add_subparsers(description='The following subcommands are available', dest='subcmd')

        start = subparser.add_parser('start', help='Create a new cluster based on profile file')
        start.add_argument('profile_file', action='store')

        # Build Docker image
        build = subparser.add_parser('build-image', help='Build a new Docker image')
        build.add_argument('dockerfile_folder', action='store', help='Local folder name which contains the Dockerfile')
        build.add_argument('image_name', action='store', help='Name of the docker image to be created on the cluster')

        # Docker image info
        image_info = subparser.add_parser('image-info', help='Gets information of a Docker image')
        image_info.add_argument('image_name', action='store', help='Name of the docker image available on the cluster')

        # Sync: put
        sync_put = subparser.add_parser('put', help='Copy a folder from local to the cluster')
        sync_put.add_argument('local_path', action='store', help='Path to the local folder')
        sync_put.add_argument('remote_path', action='store', help='Path on the shared volume', nargs='?', default='')

        # Sync: get
        sync_get = subparser.add_parser('get', help='Copy a folder from cluster to local')
        sync_get.add_argument('remote_path', action='store', help='Path on the shared volume')
        sync_get.add_argument('local_path', action='store', help='Path to the local folder')

        # ls
        ls = subparser.add_parser('ls', help='List content of the shared volume')
        ls.add_argument('remote_path', action='store', help='Path on the shared volume', nargs='?', default='')

        # rm
        rm = subparser.add_parser('rm', help='Deletes a folder on the shared volume')
        rm.add_argument('remote_path', action='store', help='Path on the shared volume')

        # workon
        workon = subparser.add_parser('workon', help='Sets a working cluster')
        workon.add_argument('cluster_name', action='store', help='Name of the cluster')

        terminate = subparser.add_parser('terminate', help='Terminate an existing cluster')
        terminate.add_argument('--confirm', dest='no_prompt', action='store_true',
            default=False, help='Immediately terminate cluster without prompting for confirmation')

        launch = subparser.add_parser('launch', help='Launch an environment from an environment file')
        launch.add_argument('environment_file', action='store')

    def _init_clusterous_object(self, args):
        app = None
        if args.verbose:
            app = clusterous.Clusterous(log_level=clusterous.Clusterous.Verbosity.DEBUG)
        else:
            app = clusterous.Clusterous()

        return app

    def _workon(self, args):
        app = self._init_clusterous_object(args)
        success, message = app.workon(cluster_name = args.cluster_name)
        print message
        return 0 if success else 1

    def _terminate_cluster(self, args):
        app = self._init_clusterous_object(args)
        cl = app.make_cluster_object()
        if not args.no_prompt:
            prompt_str = 'This will terminate the cluster {0}. Continue (y/n)? '.format(cl.cluster_name)
            cont = raw_input(prompt_str)
            if cont.lower() != 'y' and cont.lower() != 'yes':
                return 1

        app = self._init_clusterous_object(args)
        app.terminate_cluster()
        return 0

    def _launch_environment(self, args):
        app = self._init_clusterous_object(args)
        success = app.launch_environment(args.environment_file)

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

    def main(self, argv=None):
        parser = argparse.ArgumentParser('clusterous', description='Tool to create and manage compute clusters')

        self._create_args(parser)
        self._create_subparsers(parser)

        args = parser.parse_args(argv)

        status = 0


        try:
            if args.subcmd == 'start':
                app = self._init_clusterous_object(args)
                app.start_cluster(args)
            elif args.subcmd == 'terminate':
                self._terminate_cluster(args)
            elif args.subcmd == 'launch':
                self._launch_environment(args)
            elif args.subcmd == 'build-image':
                app = clusterous.Clusterous()
                app.docker_build_image(args)
            elif args.subcmd == 'image-info':
                app = clusterous.Clusterous()
                self._docker_image_info(args)
            elif args.subcmd == 'put':
                status = self._sync_put(args)
            elif args.subcmd == 'get':
                status = self._sync_get(args)
            elif args.subcmd == 'ls':
                status = self._ls(args)
            elif args.subcmd == 'rm':
                status = self._rm(args)
            elif args.subcmd == 'workon':
                status = self._workon(args)
        # TODO: this exception should not be caught here
        except NoWorkingClusterException as e:
            pass

        return status

def main(argv=None):
    cli = CLIParser()
    return cli.main(argv)
