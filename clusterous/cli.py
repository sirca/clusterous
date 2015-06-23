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
        build.add_argument('cluster_name', action='store')
        build.add_argument('dockerfile_folder', action='store')
        build.add_argument('image_name', action='store')

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

        if args.subcmd == 'build-image':
            app = clusterous.Clusterous()
            app.docker_build_image(args)

def main(argv=None):
    cli = CLIParser()
    cli.main(argv)
