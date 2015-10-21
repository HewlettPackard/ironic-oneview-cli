# -*- coding: utf-8 -*-

# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

"""
test_ironic-oneview-cli
----------------------------------

Tests for `ironic-oneview-cli` module.
"""

from ironic_oneview_cli.tests import base
from ironic_oneview_cli.facade import Facade
from ironic_oneview_cli.config import ConfClient
from ironic_oneview_cli.create_node_shell.commands import NodeCreator
from ironic_oneview_cli.objects import ServerHardwareManager
from ironic_oneview_cli.objects import ServerProfileManager

import mock
import requests
import unittest
import time 

from ironicclient import client as ironic_client

def delay(delay_time):
    time.sleep(delay_time)

class TestIronic_oneview_cli(base.TestCase):

    def setUp(self):
        defaults = {
           "ca_file": "",
           "insecure": False,
           "tls_cacert_file": "",
           "allow_insecure_connections": False,
        }
        self.config_client = ConfClient('ironic_oneview_cli/tests/'
                                   'ironic-oneview-cli-tests.conf', defaults)
        ironic_configuration_dict = self.config_client.__getattr__('ironic')

        ironic_client_kwargs = {
            'os_username': ironic_configuration_dict.admin_user,
            'os_password': ironic_configuration_dict.admin_password,
            'os_auth_url': ironic_configuration_dict.auth_uri,
            'os_tenant_name': ironic_configuration_dict.admin_tenant_name,
            'os_ironic_api_version': 1.11
        }

        self.ironic_client = ironic_client.get_client(1, **ironic_client_kwargs)
        ironic_node_list = self.ironic_client.node.list()
        for ironic_node in ironic_node_list:
            self.ironic_client.node.delete(ironic_node.uuid)
            delay(1)


    def test_list_server_hardware_not_enrolled(self):
        defaults = {
           "ca_file": "",
           "insecure": False,
           "tls_cacert_file": "",
           "allow_insecure_connections": False,
        }
        config_client = ConfClient('ironic_oneview_cli/tests/'
                                   'ironic-oneview-cli-tests.conf', defaults)
        node_creator = NodeCreator(config_client)
        hardware_manager = ServerHardwareManager(config_client)
        server_hardwares_not_enrolled = node_creator.list_server_hardware_not_enrolled(
            hardware_manager.list(only_available=True)
        )
        self.assertEqual(10, len(server_hardwares_not_enrolled))

    def test_list_server_hardware_not_enrolled_with_one_sh_already_created(self):
        defaults = {
           "ca_file": "",
           "insecure": False,
           "tls_cacert_file": "",
           "allow_insecure_connections": False,
        }
        config_client = ConfClient('ironic_oneview_cli/tests/'
                                   'ironic-oneview-cli-tests.conf', defaults)
        node_creator = NodeCreator(config_client)
        hardware_manager = ServerHardwareManager(config_client)
        profile_manager = ServerProfileManager(config_client)
        server_hardwares_not_created= node_creator.list_server_hardware_not_enrolled(
            hardware_manager.list(only_available=True)
        )
        compatible_templates = profile_manager.list_templates_compatible_with(
             server_hardwares_not_created
        )

        node = node_creator.create_node(server_hardwares_not_created[0],
                                             compatible_templates[0])
        server_hardwares_not_enrolled = node_creator.list_server_hardware_not_enrolled(
            hardware_manager.list(only_available=True)
        )
        self.assertEqual(9, len(server_hardwares_not_enrolled))
        self.ironic_client.node.delete(node.uuid)

    def test_list_templates_compatible_with(self):
        #Facade(self.config) -> mockar o self.config
        #deletar todos os ironic nodes
        #get a node_creator instance
        pass 


    def test_create_one_node(self):
        defaults = {
           "ca_file": "",
           "insecure": False,
           "tls_cacert_file": "",
           "allow_insecure_connections": False,
        }
        config_client = ConfClient('ironic_oneview_cli/tests/'
                                   'ironic-oneview-cli-tests.conf', defaults)
        node_creator = NodeCreator(config_client)
        hardware_manager = ServerHardwareManager(config_client)
        profile_manager = ServerProfileManager(config_client)
        server_hardwares_not_created= node_creator.list_server_hardware_not_enrolled(
            hardware_manager.list(only_available=True)
        )
        compatible_templates = profile_manager.list_templates_compatible_with(
             server_hardwares_not_created
        )

        node = node_creator.create_node(server_hardwares_not_created[0],
                                             compatible_templates[0])
        server_hardwares_not_created= node_creator.list_server_hardware_not_enrolled(
            hardware_manager.list(only_available=True)
        )
        self.assertEqual(9, len(server_hardwares_not_created))
        ironic_node_list = self.ironic_client.node.list()
        node_was_created = False
        for ironic_node in ironic_node_list:
            if ironic_node.uuid == node.uuid:
                node_was_created = True
                break
        self.assertEqual(node_was_created, True)
        ironic_port_list = self.ironic_client.port.list()
        self.ironic_client.node.delete(node.uuid)

if __name__ == '__main__':
    base.main() 
