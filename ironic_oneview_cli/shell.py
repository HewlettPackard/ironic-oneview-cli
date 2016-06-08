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
Command-line interface to the Ironic - HP OneView drivers.
"""

from __future__ import print_function
import argparse
import getpass
import six
import sys

from oslo_utils import encodeutils

from ironic_oneview_cli.create_flavor_shell import commands \
    as flavor_create_commands
from ironic_oneview_cli.create_node_shell import commands \
    as node_create_commands
from ironic_oneview_cli import exceptions
from ironic_oneview_cli.genrc import commands as genrc_commands
from ironic_oneview_cli.migrate_node_shell import commands \
    as node_migrate_commands
from ironic_oneview_cli.openstack.common._i18n import _
from ironic_oneview_cli.openstack.common import cliutils


VERSION = '0.0.3'

COMMAND_MODULES = [
    node_create_commands,
    flavor_create_commands,
    node_migrate_commands,
    genrc_commands
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

        # OpenStack Global arguments
        parser.add_argument('--insecure',
                            default=False,
                            action="store_true",
                            help="Explicitly allow ironic-oneview CLI to "
                            "perform \"insecure\" SSL (https) requests. The "
                            "server's certificate will not be verified "
                            "against any certificate authorities. This "
                            "option should be used with caution.")

        parser.add_argument('--os-cacert',
                            metavar='<os-ca-bundle-file>',
                            default=cliutils.env('OS_CACERT'),
                            help='Path to OpenStack CA certificate bundle '
                                 'file. Defaults to env[OS_CACERT]')

        parser.add_argument('--os_cacert',
                            help=argparse.SUPPRESS)

        parser.add_argument('-h', '--help',
                            action='store_true',
                            help=argparse.SUPPRESS,
                            )

        parser.add_argument('--version',
                            action='version',
                            version=VERSION)

        parser.add_argument('--os-username',
                            default=cliutils.env('OS_USERNAME'),
                            help='OpenStack username. '
                                 'Defaults to env[OS_USERNAME]')

        parser.add_argument('--os_username',
                            help=argparse.SUPPRESS)

        parser.add_argument('--os-password',
                            default=cliutils.env('OS_PASSWORD'),
                            help='OpenStack password. '
                                 'Defaults to env[OS_PASSWORD]')

        parser.add_argument('--os_password',
                            help=argparse.SUPPRESS)

        parser.add_argument('--os-tenant-name',
                            default=cliutils.env('OS_TENANT_NAME'),
                            help='OpenStack tenant name. '
                                 'Defaults to env[OS_TENANT_NAME]')

        parser.add_argument('--os_tenant_name',
                            help=argparse.SUPPRESS)

        parser.add_argument('--os-project-name',
                            default=cliutils.env('OS_PROJECT_NAME'),
                            help='OpenStack project name. '
                                 'Defaults to env[OS_PROJECT_NAME]')

        parser.add_argument('--os_project_name',
                            help=argparse.SUPPRESS)

        parser.add_argument('--os-auth-url',
                            default=cliutils.env('OS_AUTH_URL'),
                            help='OpenStack authentication URL. '
                                 'Defaults to env[OS_AUTH_URL]')

        parser.add_argument('--os_auth_url',
                            help=argparse.SUPPRESS)

        # OneView Global arguments
        parser.add_argument('--ov-username',
                            default=cliutils.env('OV_USERNAME'),
                            help='OneView username. '
                                 'Defaults to env[OV_USERNAME]')

        parser.add_argument('--ov_username',
                            help=argparse.SUPPRESS)

        parser.add_argument('--ov-password',
                            default=cliutils.env('OV_PASSWORD'),
                            help='OneView password. '
                                 'Defaults to env[OV_PASSWORD]')

        parser.add_argument('--ov_password',
                            help=argparse.SUPPRESS)

        parser.add_argument('--ov-auth-url',
                            default=cliutils.env('OV_AUTH_URL'),
                            help='OneView authentication URL. '
                                 'Defaults to env[OV_AUTH_URL]')

        parser.add_argument('--ov_auth_url',
                            help=argparse.SUPPRESS)

        parser.add_argument('--ov-cacert',
                            metavar='<ov-ca-bundle-file>',
                            default=cliutils.env('OV_CACERT'),
                            help='Path to OneView CA certificate bundle file. '
                                 'Defaults to env[OV_CACERT]')

        parser.add_argument('--ov_cacert',
                            help=argparse.SUPPRESS)

        # OpenStack Images arguments
        parser.add_argument('--os-ironic-node-driver',
                            default=cliutils.env('OS_IRONIC_NODE_DRIVER'),
                            help='Ironic driver for node creation. '
                                 'Defaults to env[OS_IRONIC_NODE_DRIVER]')

        parser.add_argument('--os_ironic_node_driver',
                            help=argparse.SUPPRESS)

        parser.add_argument(
            '--os-ironic-deploy-kernel-uuid',
            default=cliutils.env('OS_IRONIC_DEPLOY_KERNEL_UUID'),
            help='Ironic deploy kernel image UUID. '
                 'Defaults to env[OS_IRONIC_DEPLOY_KERNEL_UUID]'
        )

        parser.add_argument('--os_ironic_deploy_kernel_uuid',
                            help=argparse.SUPPRESS)

        parser.add_argument(
            '--os-ironic-deploy-ramdisk-uuid',
            default=cliutils.env('OS_IRONIC_DEPLOY_RAMDISK_UUID'),
            help='Ironic deploy ramdisk image UUID. '
                 'Defaults to env[OS_IRONIC_DEPLOY_RAMDISK_UUID]'
        )

        parser.add_argument('--os_ironic_deploy_ramdisk_uuid',
                            help=argparse.SUPPRESS)

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

        if args.func == genrc_commands.do_genrc:
            genrc_commands.do_genrc(args)
            return 0

        if not args.os_username:
            raise exceptions.CommandError(_("You must provide a username via "
                                            "either --os-username or via "
                                            "env[OS_USERNAME]"))

        if not (args.os_tenant_name or args.os_project_name):
            raise exceptions.CommandError(
                _("You must provide a tenant name or "
                  "project name via --os-tenant-name or --os-project-name, "
                  "env[OS_TENANT_NAME] or env[OS_PROJECT_NAME]. You may "
                  "use os-tenant and os-project interchangeably."))

        if not args.os_auth_url:
            raise exceptions.CommandError(_("You must provide an auth url via "
                                            "either --os-auth-url or via "
                                            "env[OS_AUTH_URL]"))

        if not args.os_password:
            if hasattr(sys.stdin, 'isatty') and sys.stdin.isatty():

                try:
                    args.os_password = getpass.getpass('OpenStack Password: ')

                except EOFError:
                    pass

        if not args.os_password:
            raise exceptions.CommandError(_("You must provide a password via "
                                            "either --os-password, "
                                            "env[OS_PASSWORD], "
                                            "or prompted response"))

        if not args.ov_username:
            raise exceptions.CommandError(_("You must provide a username via "
                                            "either --ov-username or via "
                                            "env[OV_USERNAME]"))

        if not args.ov_auth_url:
            raise exceptions.CommandError(_("You must provide an auth url via "
                                            "either --ov-auth-url or via "
                                            "env[OV_AUTH_URL]"))

        if not args.os_ironic_node_driver:
            raise exceptions.CommandError(_("You must provide an node driver "
                                            "via either "
                                            "--os-ironic-node-driver or via "
                                            "env[OS_IRONIC_NODE_DRIVER]"))

        if not args.os_ironic_deploy_kernel_uuid:
            raise exceptions.CommandError(
                _("You must provide a deploy "
                  "kernel uuid via either "
                  "--os-ironic-deploy-kernel-uuid "
                  "or via "
                  "env[OS_IRONIC_DEPLOY_KERNEL_UUID]")
            )

        if not args.os_ironic_deploy_ramdisk_uuid:
            raise exceptions.CommandError(
                _("You must provide a deploy ramdisk uuid via either "
                  "--os-ironic-deploy-ramdisk-uuid or via "
                  "env[OS_IRONIC_DEPLOY_RAMDISK_UUID]")
            )

        if not args.ov_password:
            if hasattr(sys.stdin, 'isatty') and sys.stdin.isatty():

                try:
                    args.ov_password = getpass.getpass('HP OneView Password: ')

                except EOFError:
                    pass

        if not args.ov_password:
            raise exceptions.CommandError(_("You must provide a password via "
                                            "either --ov-password, "
                                            "env[OV_PASSWORD], "
                                            "or prompted response"))

        client_args = (
            'os_username', 'os_password', 'os_tenant_name', 'os_project_name',
            'os_cacert', 'os_auth_url', 'ov_username', 'ov_password',
            'ov_auth_url', 'ov_cacert', 'insecure', 'os_ironic_node_driver',
            'os_ironic_deploy_kernel_uuid', 'os_ironic_deploy_ramdisk_uuid'
        )

        kwargs = {}
        for key in client_args:
            kwargs[key] = getattr(args, key)

        try:
            args.func(args)
        except exceptions.Unauthorized:
            raise exceptions.CommandError(
                _("Invalid OpenStack Identity credentials")
            )
        except exceptions.CommandError as e:
            subcommand_parser = self.subcommands[args.subparser_name]
            subcommand_parser.error(e)


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
