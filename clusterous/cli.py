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

        # Build Docker image
        build = subparser.add_parser('build-image', help='Build a new Docker image')
        build.add_argument('cluster_name', action='store', help='Name of the cluster')
        build.add_argument('dockerfile_folder', action='store', help='Local folder name which contains the Dockerfile')
        build.add_argument('image_name', action='store', help='Name of the docker image to be created on the cluster')

        # Docker image info
        image_info = subparser.add_parser('image-info', help='Gets information of a Docker image')
        image_info.add_argument('cluster_name', action='store', help='Name of the cluster')
        image_info.add_argument('image_name', action='store', help='Name of the docker image available on the cluster')

        terminate = subparser.add_parser('terminate', help='Terminate an existing cluster')
        terminate.add_argument('cluster_name', action='store')
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

    def _terminate_cluster(self, args):
        if not args.no_prompt:
            prompt_str = 'This will terminate the cluster {0}. Continue (y/n)? '.format(args.cluster_name)
            cont = raw_input(prompt_str)
            if cont.lower() != 'y' and cont.lower() != 'yes':
                return 1

        app = self._init_clusterous_object(args)
        app.terminate_cluster(args.cluster_name)
        return 0

    def _launch_environment(self, args):
        app = self._init_clusterous_object(args)
        app.launch_environment(args.environment_file)

    def _docker_image_info(self, args):
        app = self._init_clusterous_object(args)
        info = app.docker_image_info(args.cluster_name, args.image_name)
        if not info:
            print 'Docker image "{0}" does not exist in the Docker registry'.format(args.image_name)
            return 1
        else:
            print 'Docker image: {}:{}\nImage id: {}\nAuthor: {}\nCreated: {}'.format(
                info['image_name'], info['tag_name'], info['image_id'], info['author'], info['created'])
            return 0


    def main(self, argv=None):
        parser = argparse.ArgumentParser('clusterous', description='Tool to create and manage compute clusters')

        self._create_args(parser)
        self._create_subparsers(parser)

        args = parser.parse_args(argv)

        status = 0
        if args.subcmd == 'start':
            app = self._init_clusterous_object(args)
            app.start_cluster(args)
        elif args.subcmd == 'terminate':
            status = self._terminate_cluster(args)
        elif args.subcmd == 'build-image':
            app = self._init_clusterous_object(args)
            app.docker_build_image(args)
        elif args.subcmd == 'image-info':
            status = self._docker_image_info(args)
        elif args.subcmd == 'launch':
            self._launch_environment(args)

        return status

def main(argv=None):
    cli = CLIParser()
    return cli.main(argv)
