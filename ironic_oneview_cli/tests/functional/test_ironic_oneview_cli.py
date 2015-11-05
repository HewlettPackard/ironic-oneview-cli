# -*- encoding: utf-8 -*-
#
# Copyright 2015 Hewlett-Packard Development Company, L.P.
# Copyright 2015 Universidade Federal de Campina Grande
#
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
# under the License

"""
test_ironic-oneview-cli
----------------------------------

Tests for `ironic-oneview-cli` module.
"""
from ironic_oneview_cli.tests import base
from ironic_oneview_cli.facade import Facade
from ironic_oneview_cli.config import ConfClient
from ironic_oneview_cli.create_node_shell.commands import NodeCreator
from ironic_oneview_cli.create_flavor_shell import commands as flavor_commands
from ironic_oneview_cli.objects import ServerHardwareManager
from ironic_oneview_cli.objects import ServerProfileManager
from ironic_oneview_cli.create_flavor_shell.objects import Flavor

import mock
import requests
import unittest
import time

from ironicclient import client as ironic_client


TEST_CONFIG_PATH = 'ironic_oneview_cli/tests/ironic-oneview-cli-tests.conf'
# TEST_CONFIG_PATH = '~/sync.conf'

def delay(delay_time):
    time.sleep(delay_time)


class TestIronic_oneview_cli(base.TestCase):

    def setUp(self):
        self.created_nodes = []
        defaults = {
            "ca_file": "",
            "insecure": False,
            "tls_cacert_file": "",
            "allow_insecure_connections": False,
        }
        self.config_client = ConfClient('ironic_oneview_cli/tests/'
                                        'ironic-oneview-cli-tests.conf',
                                         defaults)
        ironic_configuration_dict = self.config_client.__getattr__('ironic')
        self.config = ConfClient(TEST_CONFIG_PATH, defaults)
        ironic_client_kwargs = {
            'os_username': self.config.ironic.admin_user,
            'os_password': self.config.ironic.admin_password,
            'os_auth_url': self.config.ironic.auth_url,
            'os_tenant_name': self.config.ironic.admin_tenant_name,
            'os_ironic_api_version': 1.11,
            'insecure': self.config.ironic.insecure
        }
        self.node_creator = NodeCreator(self.config_client)
        self.hardware_manager = ServerHardwareManager(self.config_client)
        self.profile_manager = ServerProfileManager(self.config_client)
        self.ironic_client = ironic_client.get_client(1, **ironic_client_kwargs)
        ironic_node_list = self.ironic_client.node.list()
        for ironic_node in ironic_node_list:
            try:
                self.ironic_client.node.delete(ironic_node.uuid)
            except Exception:
                continue
        self.ironic_client = ironic_client.get_client(1,
                                                      **ironic_client_kwargs)

    def tearDown(self):
        while self.created_nodes:
            node_uuid = self.created_nodes.pop()
            self.ironic_client.node.delete(node_uuid)

    def test_list_server_hardware_not_enrolled(self):
        node_creator = NodeCreator(self.config)
        hardware_manager = ServerHardwareManager(self.config)
        server_hardwares_not_enrolled = node_creator.list_server_hardware_not_enrolled(
            hardware_manager.list(only_available=True)
        )
        self.assertEqual(10, len(server_hardwares_not_enrolled))

    def test_list_server_hardware_not_enrolled_with_one_sh_already_created(self):
        node_creator = NodeCreator(self.config)
        hardware_manager = ServerHardwareManager(self.config)
        profile_manager = ServerProfileManager(self.config)
        server_hardwares_not_created = node_creator.list_server_hardware_not_enrolled(
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

    def test_create_one_node(self):
        node_creator = NodeCreator(self.config)
        hardware_manager = ServerHardwareManager(self.config)
        profile_manager = ServerProfileManager(self.config)
        server_hardwares_not_created = node_creator.list_server_hardware_not_enrolled(
            hardware_manager.list(only_available=True)
        )
        compatible_templates = profile_manager.list_templates_compatible_with(
            server_hardwares_not_created
        )

        node = node_creator.create_node(server_hardwares_not_created[0],
                                        compatible_templates[0])
        self.created_nodes.append(node.uuid)
        server_hardwares_not_created = node_creator.list_server_hardware_not_enrolled(
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

    def test_get_flavor_name(self):
        flavor_info = {'cpu_arch':'x64', 'ram_mb':'32000',
                       'cpus':'8', 'disk':'120'}
        flavor = Flavor(1, flavor_info)
        flavor_name = flavor_commands._get_flavor_name(flavor)
        self.assertEqual('32000MB-RAM_8_x64_120', flavor_name)

    def test_get_flavor_from_ironic_node(self):
        server_hardwares_not_created = self.node_creator.list_server_hardware_not_enrolled(
            self.hardware_manager.list(only_available=True)
        )
        server_hardware_for_test = server_hardwares_not_created[0]
        compatible_templates = self.profile_manager.list_templates_compatible_with(
            server_hardwares_not_created
        )
        node = self.node_creator.create_node(server_hardware_for_test,
                                             compatible_templates[0])
        server_profile_for_test = compatible_templates[0]
        flavor = flavor_commands.get_flavor_from_ironic_node(1, node)
        self.assertEqual(server_hardware_for_test.memoryMb, flavor.ram_mb)
        self.assertEqual(server_hardware_for_test.cpus, flavor.cpus)
        self.assertEqual(120, flavor.disk)
        self.assertEqual(server_hardware_for_test.cpu_arch, flavor.cpu_arch)
        self.assertEqual(server_hardware_for_test.serverHardwareTypeUri,
                         flavor.server_hardware_type_uri)
        self.assertEqual(server_hardware_for_test.serverGroupUri,
                         flavor.enclosure_group_uri)
        self.assertEqual(server_profile_for_test.uri,
                         flavor.server_profile_template_uri)

    def test_create_node_retrieve_n_check(self):
        node_creator = NodeCreator(self.config)
        hardware_manager = ServerHardwareManager(self.config)
        profile_manager = ServerProfileManager(self.config)
        server_hardwares_not_created = node_creator.list_server_hardware_not_enrolled(
            hardware_manager.list(only_available=True)
        )
        hardware_selected = server_hardwares_not_created[0]
        compatible_templates = profile_manager.list_templates_compatible_with(
            server_hardwares_not_created
        )
        template_selected = compatible_templates[0]

        node = node_creator.create_node(hardware_selected, template_selected)
        self.created_nodes.append(node.uuid)

        self.assertEquals(node.driver_info.get('server_hardware_uri'),
                          hardware_selected.uri)
        self.assertEquals(node.driver_info.get('deploy_kernel'),
                          self.config.ironic.default_deploy_kernel_id)
        self.assertEquals(node.driver_info.get('deploy_ramdisk'),
                          self.config.ironic.default_deploy_ramdisk_id)
        capabilities = node.properties.get('capabilities')
        self.assertIn('server_profile_template_uri:' + template_selected.uri,
                      capabilities)

if __name__ == '__main__':
    base.main()

