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

import mock
import unittest

from ironic_oneview_cli.create_flavor_shell.commands import FlavorCreator
from ironic_oneview_cli.create_node_shell.commands import NodeCreator
from ironic_oneview_cli import facade
from ironic_oneview_cli.tests.stubs import StubIronicNode
from ironic_oneview_cli.tests.stubs import StubParameters
from ironic_oneview_cli.tests.stubs import StubNovaFlavor
from ironic_oneview_cli.tests.stubs import StubServerHardware
from ironic_oneview_cli.tests.stubs import StubServerProfileTemplate


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


POOL_OF_STUB_SERVER_PROFILE_TEMPLATE = [
    StubServerProfileTemplate(
        uri='/rest/server-profile-templates/huehuehuehuehue',
        server_hardware_type_uri='/rest/server-hadware-types/huehuehuehuehue',
        enclosure_group_uri='/rest/enclosure-groups/huehuehuehuehue',
        connections=[],
        boot={}
    )
]


POOL_OF_STUB_NOVA_FLAVORS = [
    StubNovaFlavor(
        id=123,
        uuid='66666666-7777-8888-9999-000000000000',
        name='fake-flavor',
        memory_mb=1024,
        vcpus=1,
        root_gb=100,
        ephemeral_gb=0,
        flavorid='abc',
        swap=0,
        rxtx_factor=1,
        vcpu_weight=1,
        disabled=False,
        is_public=True,
        extra_specs={},
        projects=[]
    )
]


STUB_PARAMETERS = StubParameters(
    os_ironic_node_driver='fake',
    os_ironic_deploy_kernel_uuid='11111-22222-33333-44444-55555',
    os_ironic_deploy_ramdisk_uuid='55555-44444-33333-22222-11111'
)


class FunctionalTestIronicOneviewCli(unittest.TestCase):

    @mock.patch.object(facade.Facade, 'create_ironic_node')
    @mock.patch('ironic_oneview_cli.facade.Facade')
    def test_node_creation(self, mock_facade, mock_create_ironic_node):

        ironic_node = POOL_OF_STUB_IRONIC_NODES[0]
        mock_create_ironic_node.return_value = ironic_node
        mock_facade.create_ironic_node = mock_create_ironic_node

        node_creator = NodeCreator(mock_facade)
        node_creator.create_node(STUB_PARAMETERS,
                                 POOL_OF_STUB_SERVER_HARDWARE[0],
                                 POOL_OF_STUB_SERVER_PROFILE_TEMPLATE[0])

        attrs = {
            'driver': STUB_PARAMETERS.os_ironic_node_driver,
            'driver_info': {
                'deploy_kernel': STUB_PARAMETERS.os_ironic_deploy_kernel_uuid,
                'deploy_ramdisk': STUB_PARAMETERS.os_ironic_deploy_ramdisk_uuid,
                'server_hardware_uri':
                    POOL_OF_STUB_SERVER_HARDWARE[0].uri,
            },
            'properties': {
                'cpus': POOL_OF_STUB_SERVER_HARDWARE[0].cpus,
                'memory_mb': POOL_OF_STUB_SERVER_HARDWARE[0].memory_mb,
                'local_gb': POOL_OF_STUB_SERVER_HARDWARE[0].local_gb,
                'cpu_arch': POOL_OF_STUB_SERVER_HARDWARE[0].cpu_arch,
                'capabilities': 'server_hardware_type_uri:%s,'
                                'enclosure_group_uri:%s,'
                                'server_profile_template_uri:%s' % (
                                    POOL_OF_STUB_SERVER_HARDWARE[0].serverHardwareTypeUri,
                                    POOL_OF_STUB_SERVER_HARDWARE[0].serverGroupUri,
                                    POOL_OF_STUB_SERVER_PROFILE_TEMPLATE[0].uri
                )
            }
        }

        mock_create_ironic_node.assert_called_with(
            **attrs
        )

    @mock.patch.object(facade.Facade, 'create_nova_flavor')
    @mock.patch('ironic_oneview_cli.facade.Facade')
    def test_flavor_creation(self, mock_facade, mock_create_nova_flavor):

        nova_flavor = POOL_OF_STUB_NOVA_FLAVORS[0]
        nova_flavor.set_keys = lambda extra_specs: None
        mock_create_nova_flavor.return_value = nova_flavor
        mock_facade.create_nova_flavor = mock_create_nova_flavor

        flavor_creator = FlavorCreator(mock_facade)
        flavor_creator.create_flavor(
            POOL_OF_STUB_NOVA_FLAVORS[0].name,
            POOL_OF_STUB_NOVA_FLAVORS[0].memory_mb,
            POOL_OF_STUB_NOVA_FLAVORS[0].vcpus,
            POOL_OF_STUB_NOVA_FLAVORS[0].root_gb,
            POOL_OF_STUB_NOVA_FLAVORS[0].extra_specs
        )

        attrs = {
            'name': POOL_OF_STUB_NOVA_FLAVORS[0].name,
            'ram': POOL_OF_STUB_NOVA_FLAVORS[0].memory_mb,
            'vcpus': POOL_OF_STUB_NOVA_FLAVORS[0].vcpus,
            'disk': POOL_OF_STUB_NOVA_FLAVORS[0].root_gb
        }

        mock_create_nova_flavor.assert_called_with(
            **attrs
        )



if __name__ == '__main__':
    unittest.main()
