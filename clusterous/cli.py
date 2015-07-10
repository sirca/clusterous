import sys
import argparse

import clusterous


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

        # Build dokcer image
        build = subparser.add_parser('build-image', help='Build a new Docker image')
        build.add_argument('cluster_name', action='store', help='Name of the cluster')
        build.add_argument('dockerfile_folder', action='store', help='Local folder name which contains the Dockerfile')
        build.add_argument('image_name', action='store', help='Name of the docker image to be created on the cluster')

        # Docker image info
        image_info = subparser.add_parser('image-info', help='Gets information of a Docker image')
        image_info.add_argument('cluster_name', action='store', help='Name of the cluster')
        image_info.add_argument('image_name', action='store', help='Name of the docker image available on the cluster')

        # Sync: put
        sync_put = subparser.add_parser('put', help='Copy a folder from local to the cluster')
        sync_put.add_argument('cluster_name', action='store', help='Name of the cluster')
        sync_put.add_argument('local_path', action='store', help='Path to the local folder')
        sync_put.add_argument('remote_path', action='store', help='Path on the shared volume', nargs='?', default='')

        # Sync: get
        sync_get = subparser.add_parser('get', help='Copy a folder from cluster to local')
        sync_get.add_argument('cluster_name', action='store', help='Name of the cluster')
        sync_get.add_argument('remote_path', action='store', help='Path on the shared volume')
        sync_get.add_argument('local_path', action='store', help='Path to the local folder')

        # ls
        ls = subparser.add_parser('ls', help='List content of the shared volume')
        ls.add_argument('cluster_name', action='store', help='Name of the cluster')
        ls.add_argument('remote_path', action='store', help='Path on the shared volume', nargs='?', default='')

        terminate = subparser.add_parser('terminate', help='Terminate an existing cluster')
        terminate.add_argument('cluster_name', action='store')
        terminate.add_argument('--confirm', dest='no_prompt', action='store_true',
            default=False, help='Immediately terminate cluster without prompting for confirmation')

    def _init_clusterous_object(self, args):
        app = None
        if args.verbose:
            app = clusterous.Clusterous(log_level=clusterous.Clusterous.Verbosity.DEBUG)
        else:
            app = clusterous.Clusterous()

        return app

    def _terminate_cluster(self, args):
        if not args.no_prompt:
            prompt_str = 'This will terminate the cluster {0}. Continue (y/n)? '.format(args.cluster_name)
            cont = raw_input(prompt_str)
            if cont.lower() != 'y' and cont.lower() != 'yes':
                sys.exit(0)

        app = self._init_clusterous_object(args)
        app.terminate_cluster(args.cluster_name)

    def _sync_put(self, args):
        app = self._init_clusterous_object(args)
        success, message = app.sync_put(cluster_name = args.cluster_name, 
                                        local_path = args.local_path, 
                                        remote_path = args.remote_path)
        if not success:
            print message
            return 1
        return 0

    def _sync_get(self, args):
        app = self._init_clusterous_object(args)
        success, message = app.sync_get(cluster_name = args.cluster_name, 
                                        remote_path = args.remote_path,
                                        local_path = args.local_path)
        if not success:
            print message
            return 1
        return 0
    
    def _ls(self, args):
        app = self._init_clusterous_object(args)
        success, message = app.ls(cluster_name = args.cluster_name, 
                                        remote_path = args.remote_path)
        print message
        return 0 if success else 1


    def main(self, argv=None):
        parser = argparse.ArgumentParser('clusterous', description='Tool to create and manage compute clusters')

        self._create_args(parser)
        self._create_subparsers(parser)

        args = parser.parse_args(argv)

        if args.subcmd == 'start':
            app = self._init_clusterous_object(args)
            app.start_cluster(args)
        elif args.subcmd == 'terminate':
            self._terminate_cluster(args)
        elif args.subcmd == 'build-image':
            app = clusterous.Clusterous()
            app.docker_build_image(args)
        elif args.subcmd == 'image-info':
            app = clusterous.Clusterous()
            app.docker_image_info(args)
        elif args.subcmd == 'put':
            status = self._sync_put(args)
        elif args.subcmd == 'get':
            status = self._sync_get(args)
        elif args.subcmd == 'ls':
            status = self._ls(args)

def main(argv=None):
    cli = CLIParser()
    cli.main(argv)
