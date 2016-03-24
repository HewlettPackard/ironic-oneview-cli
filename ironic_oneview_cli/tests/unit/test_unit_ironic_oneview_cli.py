# -*- encoding: utf-8 -*-
#
# Copyright 2016 Hewlett-Packard Development Company, L.P.
# Copyright 2016 Universidade Federal de Campina Grande
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

import mock
import unittest

from ironic_oneview_cli import facade
from ironic_oneview_cli.create_node_shell.commands import NodeCreator
from ironic_oneview_cli.tests.stubs import StubNovaFlavor
from ironic_oneview_cli.tests.stubs import StubIronicNode
from ironic_oneview_cli.tests.stubs import StubServerHardware

POOL_OF_STUB_IRONIC_NODES = [
    StubIronicNode(
        id=001,
        uuid='111111111-2222-8888-9999-000000000000',
        chassis_uuid='aaaaaaaa-1111-bbbb-2222-cccccccccccc',
        maintenance=False,
        provision_state='enroll',
        ports=[
            {'id': 987,
             'uuid': '11111111-2222-3333-4444-555555555555',
             'node_uuid': '66666666-7777-8888-9999-000000000000',
             'address': 'AA:BB:CC:DD:EE:FF',
             'extra': {}}
        ],
        driver='fake_oneview',
        driver_info={'user': 'foo', 'password': 'bar'},
        properties={'num_cpu': 4},
        name='fake-node-1',
        extra={}
    ),
    StubIronicNode(
        id=002,
        uuid='22222222-3333-8888-9999-000000000000',
        chassis_uuid='aaaaaaaa-1111-bbbb-2222-cccccccccccc',
        maintenance=False,
        provision_state='enroll',
        ports=[
            {'id': 987,
             'uuid': '11111111-2222-3333-4444-555555555555',
             'node_uuid': '66666666-7777-8888-9999-000000000000',
             'address': 'AA:BB:CC:DD:EE:FF',
             'extra': {}}
        ],
        driver='fake_oneview',
        driver_info={'server_hardware_uri': "/rest/server-hardware/22222",
                     'user': 'foo',
                     'password': 'bar'
        },
        properties={'num_cpu': 4},
        name='fake-node-1',
        extra={}
    )
]


POOL_OF_STUB_SERVER_HARDWARE = [
    StubServerHardware(
        uuid='11111111-7777-8888-9999-000000000000',
        uri='/rest/server-hardware/11111',
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
    ),
    StubServerHardware(
        uuid='22222222-7777-8888-9999-000000000000',
        uri='/rest/server-hardware/22222',
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

POOL_OF_STUB_NOVA_FLAVORS = [
    StubNovaFlavor(
       ram_mb='32000',
       cpus='8',
       cpu_arch='x64',
       disk='120'
    )
]


class UnitTestIronicOneviewCli(unittest.TestCase):

    @mock.patch.object(facade.Facade, 'get_ironic_node_list')
    @mock.patch('ironic_oneview_cli.facade.Facade')
    def test_list_server_hardware_not_enrolled(self,
                                               mock_facade,
                                               mock_ironic_node_list):
        
        node_creator = NodeCreator(mock_facade)

        ironic_nodes = POOL_OF_STUB_IRONIC_NODES
        mock_ironic_node_list.return_value = ironic_nodes
        mock_facade.get_ironic_node_list = mock_ironic_node_list

        not_enrolled = node_creator.list_server_hardware_not_enrolled(
            POOL_OF_STUB_SERVER_HARDWARE
        )

        self.assertEqual(1, len(not_enrolled))


    @mock.patch('ironic_oneview_cli.facade.Facade')
    def test_generate_flavor_name(self, mock_facade):

        flavor_creator = FlavorCreator(mock_facade)
        flavor_name = flavor_creator.get_flavor_name(POOL_OF_STUB_NOVA_FLAVORS[0])
        self.assertEqual('32000MB-RAM_8_x64_120', flavor_name) 

if __name__ == '__main__':
    unittest.main()
