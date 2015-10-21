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


import argparse
from ironicclient import exc
from service.create_node_shell import ov_create_node
import unittest


class Command:
    def __init__(self, command):
        self.command = command


class CreateServiceTestCase(unittest.TestCase):

    def setUp(self):
        self.oneview_shell = create_service.OneViewSyncShell()


    def test_get_base_parser_and_get_subcommand_parser(self):
        parser = self.oneview_shell.get_base_parser()
        self.assertEquals(parser.prog, 'create-service')
        self.assertEquals(parser.epilog, 'See "ov-flavor help COMMAND" for help on a specific command.')
        self.assertIsNone(parser._subparsers)

        parser_with_subcommand = self.oneview_shell.get_subcommand_parser(None)
        self.assertIsNotNone(parser_with_subcommand._subparsers)


    def test_do_help_passing_None(self):
        self.assertRaises(AttributeError, self.oneview_shell.do_help, None)
    

    def test_do_help_passing_invalid_args(self):
        self.assertRaises(AttributeError, self.oneview_shell.do_help, 'any')


    def test_do_help_passing_invalid_command(self):
        args = Command("any_wrong_command")
        self.oneview_shell.get_subcommand_parser(1)
        self.assertRaises(exc.CommandError, self.oneview_shell.do_help, args)


    def test_do_help_passing_valid_command(self):
        args = Command("node-create")
        self.oneview_shell.get_subcommand_parser(1)
        self.oneview_shell.do_help(args)
