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

import os
import time
import unittest

from mock import patch

from ironicclient import client as ironic_client



from ironic_oneview_cli.create_flavor_shell import commands as flavor_commands
from ironic_oneview_cli.create_flavor_shell.objects import Flavor

from ironic_oneview_cli.create_node_shell.commands import NodeCreator
from ironic_oneview_cli.create_node_shell.commands import do_node_create


from ironic_oneview_cli.objects import ServerHardwareManager
from ironic_oneview_cli.objects import ServerProfileManager

from ironic_oneview_cli.tests import base


from ironic_oneview_cli import facade

class FakeServerHardware(object):

    def __init__(self, uuid, uri, power_state, server_profile_uri,
                 server_hardware_type_uri, serverHardwareTypeUri,
                 enclosure_group_uri, serverGroupUri, status, state,
                 state_reason, enclosure_uri, local_gb, cpu_arch, cpus,
                 processor_count, processor_core_count, memoryMb, memory_mb, 
                 port_map, mp_host_info):

        self.uuid = uuid
        self.uri = uri
        self.power_state = power_state
        self.server_profile_uri = server_profile_uri
        self.server_hardware_type_uri = server_hardware_type_uri
        self.serverHardwareTypeUri = serverHardwareTypeUri # remove before python-oneviewclient
        self.serverGroupUri = serverGroupUri # remove before python-oneviewclient
        self.enclosure_group_uri = enclosure_group_uri
        self.status = status
        self.state = state
        self.state_reason = state_reason
        self.enclosure_uri = enclosure_uri
        self.local_gb = local_gb # remove before python-oneviewclient
        self.cpu_arch = cpu_arch # remove before python-oneviewclient
        self.cpus = cpus # remove before python-oneviewclient
        self.processor_count = processor_count
        self.processor_core_count = processor_core_count
        self.memoryMb = memoryMb # remove before python-oneviewclient
        self.memory_mb = memory_mb
        self.port_map = port_map
        self.mp_host_info = mp_host_info


class FakeServerProfileTemplate(object):

    def __init__(self, uri, server_hardware_type_uri, enclosure_group_uri,
                 connections, boot):

        self.uri = uri
        self.server_hardware_type_uri = server_hardware_type_uri
        self.enclosure_group_uri = enclosure_group_uri
        self.connections = connections
        self.boot = boot


POOL_OF_FAKE_SERVER_HARDWARE = [
    FakeServerHardware(
        uuid='66666666-7777-8888-9999-000000000000',
        uri='/rest/server-hardware/huehuehuehuehue',
        power_state='Off',
        server_profile_uri='',
        server_hardware_type_uri='/rest/server-hardware-types/huehuehuehuehue',
        serverHardwareTypeUri='/rest/server-hardware-types/huehuehuehuehue',
        serverGroupUri='/rest/enclosure-groups/huehuehuehuehue',
        enclosure_group_uri='/rest/enclosure-groups/huehuehuehuehue',
        status='OK',
        state='Unknown',
        state_reason='',
        enclosure_uri='/rest/enclosures/huehuehuehuehue',
        local_gb=72768,
        cpu_arch='x86_64',
        cpus=12,
        processor_count=12,
        processor_core_count=12,
        memoryMb=16384,
        memory_mb=16384,
        port_map=[],
        mp_host_info={}
    )
]


POOL_OF_FAKE_SERVER_PROFILE_TEMPLATE = [
    FakeServerProfileTemplate(
        uri='/rest/server-profile-templates/huehuehuehuehue',
        server_hardware_type_uri='/rest/server-hadware-types/huehuehuehuehue',
        enclosure_group_uri='/rest/enclosure-groups/huehuehuehuehue',
        connections=[],
        boot={}
    )
]


class TestIronicOneviewCli(base.TestCase):

    def setUp(self):

        os.environ['OS_AUTH_URL'] = 'https://192.168.0.1'
        os.environ['OS_USERNAME'] = 'username'
        os.environ['OS_PASSWORD'] = 'password'
        os.environ['OS_PROJECT_NAME'] = 'demo'
        os.environ['OS_TENANT_NAME'] = 'demo'
        os.environ['OS_CACERT'] = ''
        os.environ['OS_IRONIC_DEPLOY_KERNEL_UUID'] = 'aaaaa-bbbbb-ccccc-ddddd'
        os.environ['OS_IRONIC_DEPLOY_RAMDISK_UUID'] = 'ddddd-ccccc-bbbbb-aaaaa'
        os.environ['OS_IRONIC_NODE_DRIVER'] = 'agent_pxe_oneview'

        os.environ['OV_AUTH_URL'] = 'https://192.168.0.2'
        os.environ['OV_USERNAME'] = 'admin'
        os.environ['OV_PASSWORD'] = 'password'
        os.environ['OV_CACERT'] = ''

        


        self.nodes = []
        self.flavors = []


    def tearDown(self):

        del os.environ['OS_AUTH_URL']
        del os.environ['OS_USERNAME']
        del os.environ['OS_PASSWORD']
        del os.environ['OS_PROJECT_NAME']
        del os.environ['OS_TENANT_NAME']
        del os.environ['OS_CACERT']
        del os.environ['OS_IRONIC_DEPLOY_KERNEL_UUID']
        del os.environ['OS_IRONIC_DEPLOY_RAMDISK_UUID']
        del os.environ['OS_IRONIC_NODE_DRIVER']

        del os.environ['OV_AUTH_URL']
        del os.environ['OV_USERNAME']
        del os.environ['OV_PASSWORD']
        del os.environ['OV_CACERT']

        #TODO Delete created data

    @patch.object(facade.Facade, 'create_ironic_node')
    @patch('ironic_oneview_cli.facade.Facade')
    def test_node_creation(self, mock_facade, mock_create_ironic_node):
         
        mock_facade.ironicclient = None
        mock_facade.novaclient = None
        mock_facade.ovclient = None

        node_created = True
        mock_create_ironic_node.return_value = node_created
        mock_facade.create_ironic_node = mock_create_ironic_node

        node_creator = NodeCreator(mock_facade)
        node_creator.create_node(POOL_OF_FAKE_SERVER_HARDWARE[0],
                                      POOL_OF_FAKE_SERVER_PROFILE_TEMPLATE[0])

        attrs = {
            'driver': os.environ['OS_IRONIC_NODE_DRIVER'],
            'driver_info': {
                'deploy_kernel': os.environ['OS_IRONIC_DEPLOY_KERNEL_UUID'],
                'deploy_ramdisk': os.environ['OS_IRONIC_DEPLOY_RAMDISK_UUID'],
                'server_hardware_uri':
                    POOL_OF_FAKE_SERVER_HARDWARE[0].uri,
            },
            'properties': {
                'cpus': POOL_OF_FAKE_SERVER_HARDWARE[0].cpus,
                'memory_mb': POOL_OF_FAKE_SERVER_HARDWARE[0].memory_mb,
                'local_gb': POOL_OF_FAKE_SERVER_HARDWARE[0].local_gb,
                'cpu_arch': POOL_OF_FAKE_SERVER_HARDWARE[0].cpu_arch,
                'capabilities': 'server_hardware_type_uri:%s,'
                                'enclosure_group_uri:%s,'
                                'server_profile_template_uri:%s' % (
                                    POOL_OF_FAKE_SERVER_HARDWARE[0].serverHardwareTypeUri,
                                    POOL_OF_FAKE_SERVER_HARDWARE[0].serverGroupUri,
                                    POOL_OF_FAKE_SERVER_PROFILE_TEMPLATE[0].uri,
                                )
            }
        }

        mock_create_ironic_node.assert_called_with(
            **attrs
        )

    def test_flavor_creation(self):
        pass


if __name__ == '__main__':
    unittest.main()

'''
base.main()

    def test_list_server_hardware_not_enrolled(self):
        node_creator = NodeCreator(self.config)
        hardware_manager = ServerHardwareManager(self.config)
        server_hardwares_not_enrolled = (
            node_creator.list_server_hardware_not_enrolled(
                hardware_manager.list(only_available=True)
            )
        )
        self.assertEqual(10, len(server_hardwares_not_enrolled))

    def test_list_server_hardware_not_enrolled_with_one_sh_already_created(
            self):
        node_creator = NodeCreator(self.config)
        hardware_manager = ServerHardwareManager(self.config)
        profile_manager = ServerProfileManager(self.config)
        server_hardwares_not_created = (
            node_creator.list_server_hardware_not_enrolled(
                hardware_manager.list(only_available=True)
            )
        )
        compatible_templates = profile_manager.list_templates_compatible_with(
            server_hardwares_not_created
        )

        node = node_creator.create_node(server_hardwares_not_created[0],
                                        compatible_templates[0])
        server_hardwares_not_enrolled = (
            node_creator.list_server_hardware_not_enrolled(
                hardware_manager.list(only_available=True)
            )
        )
        self.assertEqual(9, len(server_hardwares_not_enrolled))
        self.ironic_client.node.delete(node.uuid)

    def test_create_one_node(self):
        node_creator = NodeCreator(self.config)
        hardware_manager = ServerHardwareManager(self.config)
        profile_manager = ServerProfileManager(self.config)
        server_hardwares_not_created = (
            node_creator.list_server_hardware_not_enrolled(
                hardware_manager.list(only_available=True)
            )
        )
        compatible_templates = profile_manager.list_templates_compatible_with(
            server_hardwares_not_created
        )

        node = node_creator.create_node(server_hardwares_not_created[0],
                                        compatible_templates[0])
        self.created_nodes.append(node.uuid)
        server_hardwares_not_created = (
            node_creator.list_server_hardware_not_enrolled(
                hardware_manager.list(only_available=True)
            )
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
        flavor_info = {'cpu_arch': 'x64', 'ram_mb': '32000',
                       'cpus': '8', 'disk': '120'}
        flavor = Flavor(1, flavor_info)
        flavor_name = flavor_commands._get_flavor_name(flavor)
        self.assertEqual('32000MB-RAM_8_x64_120', flavor_name)

    def test_get_flavor_from_ironic_node(self):
        server_hardwares_not_created = (
            self.node_creator.list_server_hardware_not_enrolled(
                self.hardware_manager.list(only_available=True)
            )
        )
        server_hardware_for_test = server_hardwares_not_created[0]
        compatible_templates = (
            self.profile_manager.list_templates_compatible_with(
                server_hardwares_not_created
            )
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
        server_hardwares_not_created = (
            node_creator.list_server_hardware_not_enrolled(
                hardware_manager.list(only_available=True)
            )
        )
        hardware_selected = server_hardwares_not_created[0]
        compatible_templates = profile_manager.list_templates_compatible_with(
            server_hardwares_not_created
        )
        template_selected = compatible_templates[0]

        node = node_creator.create_node(hardware_selected, template_selected)
        self.created_nodes.append(node.uuid)

        self.assertEqual(node.driver_info.get('server_hardware_uri'),
                         hardware_selected.uri)
        self.assertEqual(node.driver_info.get('deploy_kernel'),
                         self.config.ironic.default_deploy_kernel_id)
        self.assertEqual(node.driver_info.get('deploy_ramdisk'),
                         self.config.ironic.default_deploy_ramdisk_id)
        capabilities = node.properties.get('capabilities')
        self.assertIn('server_profile_template_uri:' + template_selected.uri,
                      capabilities)

    def test_create_flavor_with_server_hadware_type_enclosure_group_server_profile_template_name_is_not_empty(self):
        flavors = flavor_commands.get_flavor_list(self.ironic_client, self.hardware_manager, self.profile_manager)
        for flavor in flavors:
            self.assertNotEqual("", flavor['server_hardware_type_name'])
	    self.assertNotEqual("", flavor['enclosure_group_name'])
	    self.assertNotEqual("", flavor['server_profile_template_name'])

    def test_create_flavor_with_server_hadware_type_enclosure_group_server_profile_template_name_is_not_none(self):
        flavors = flavor_commands.get_flavor_list(self.ironic_client, self.hardware_manager, self.profile_manager)
        for flavor in flavors:
            self.assertNotNone(flavor['server_hardware_type_name'])
	    self.assertNotNone(flavor['enclosure_group_name'])
	    self.assertNotNone(flavor['server_profile_template_name'])



if __name__ == '__main__':
    base.main()
'''
