import sys
import argparse

import clusterous


class CLIParser(object):
    """
    Clusterous Command Line Interface
    """

    def __init__(self):
        pass

    def _create_subparsers(self, parser):
        subparser = parser.add_subparsers(description='The following subcommands are available', dest='subcmd')

        start = subparser.add_parser('start', help='Create a new cluster based on profile file')
        start.add_argument('profile_file', action='store')



    def main(self, argv=None):
        parser = argparse.ArgumentParser('clusterous', description='Tool to create and manage compute clusters')

        self._create_subparsers(parser)

        args = parser.parse_args(argv)

        print args
        if args.subcmd == 'start':
            app = clusterous.Clusterous()

            #print 'Starting cluster!'


def main(argv=None):
    cli = CLIParser()
    cli.main(argv)

