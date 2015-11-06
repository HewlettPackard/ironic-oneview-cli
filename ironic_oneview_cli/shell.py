# -*- encoding: utf-8 -*-
#
# Copyright 2015 Hewlett-Packard Development Company, L.P.
# Copyright 2015 Universidade Federal de Campina Grande
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
"""
Command-line interface to the OneView Sync.
"""

from __future__ import print_function
import argparse
import six
import sys

from oslo_utils import encodeutils

from ironic_oneview_cli.create_flavor_shell import commands \
    as flavor_create_commands
from ironic_oneview_cli.create_node_shell import commands \
    as node_create_commands
from ironic_oneview_cli.genconfig import commands as genconfig_commands
from ironic_oneview_cli.openstack.common._i18n import _
from ironic_oneview_cli.openstack.common import cliutils


VERSION = '1.0'

COMMAND_MODULES = [
    node_create_commands,
    flavor_create_commands,
    genconfig_commands
]


class IronicOneView(object):

    def get_base_parser(self):
        parser = argparse.ArgumentParser(
            prog='ironic-oneview',
            description=__doc__.strip(),
            epilog='See "ironic-oneview --help COMMAND" '
                   'for help on a specific command.',
            add_help=False,
            formatter_class=HelpFormatter,
        )

        # Global arguments
        parser.add_argument('-h', '--help',
                            action='store_true',
                            help=argparse.SUPPRESS,
                            )

        parser.add_argument('--version',
                            action='version',
                            version=VERSION)

        parser.add_argument('-c', '--config-file',
                            default='~/ironic-oneview-cli.conf',
                            help=('Default path to configuration file. '
                                  'Defaults to `~/ironic-oneview-cli.conf`'))

        return parser

    def get_subcommand_parser(self, version):
        parser = self.get_base_parser()
        self.subcommands = {}
        subparsers = parser.add_subparsers(metavar='<subcommand>')
        enhance_parser(parser, subparsers, self.subcommands)
        define_commands_from_module(subparsers, self, self.subcommands)
        return parser

    @cliutils.arg('command', metavar='<subcommand>', nargs='?',
                  help='Display help for <subcommand>')
    def do_help(self, args):
        """Displays help about this program or one of its subcommands."""
        if getattr(args, 'command', None):
            if args.command in self.subcommands:
                self.subcommands[args.command].print_help()
            else:
                raise Exception(_("'%s' is not a valid subcommand") %
                                args.command)
        else:
            self.parser.print_help()

    def main(self, argv):
        parser = self.get_base_parser()
        (options, args) = parser.parse_known_args(argv)
        subcommand_parser = self.get_subcommand_parser(1)
        self.parser = subcommand_parser

        if options.help or not argv:
            self.do_help(options)
            return 0

        args = subcommand_parser.parse_args(argv)
        # Short-circuit and deal with these commands right away.
        if args.func == self.do_help:
            self.do_help(args)
            return 0
        args.func(args)


def define_command(subparsers, command, callback, cmd_mapper):
    """Defines a command in the subparsers collection.

    :param subparsers: subparsers collection where the command will go
    :param command: command name
    :param callback: function that will be used to process the command

    """
    desc = callback.__doc__ or ''
    help = desc.strip().split('\n')[0]
    arguments = getattr(callback, 'arguments', [])

    subparser = subparsers.add_parser(command, help=help,
                                      description=desc,
                                      add_help=False,
                                      formatter_class=HelpFormatter)
    subparser.add_argument('-h', '--help', action='help',
                           help=argparse.SUPPRESS)
    cmd_mapper[command] = subparser
    for (args, kwargs) in arguments:
        subparser.add_argument(*args, **kwargs)
    subparser.set_defaults(func=callback)


def define_commands_from_module(subparsers, command_module, cmd_mapper):
    """Adds *do_* methods in a module and add as commands into a subparsers."""

    for method_name in (a for a in dir(command_module) if a.startswith('do_')):
        # Commands should be hypen-separated instead of underscores.
        command = method_name[3:].replace('_', '-')
        callback = getattr(command_module, method_name)
        define_command(subparsers, command, callback, cmd_mapper)


def enhance_parser(parser, subparsers, cmd_mapper):
    for command_module in COMMAND_MODULES:
        define_commands_from_module(subparsers, command_module, cmd_mapper)


class HelpFormatter(argparse.HelpFormatter):
    def start_section(self, heading):
        # Title-case the headings
        heading = '%s%s' % (heading[0].upper(), heading[1:])
        super(HelpFormatter, self).start_section(heading)


def main():
    try:
        IronicOneView().main(sys.argv[1:])
    except KeyboardInterrupt:
        print("... terminating OneView node creation tool", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(encodeutils.safe_encode(six.text_type(e)), file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
