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
import mock
import unittest

from ironic_oneview_cli.create_flavor_shell import \
    commands as create_flavor_cmd
from ironic_oneview_cli.create_node_shell import commands as create_node_cmd
from ironic_oneview_cli.tests import stubs


POOL_OF_STUB_IRONIC_NODES = [
    stubs.StubIronicNode(
        id=1,
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
    stubs.StubIronicNode(
        id=2,
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
                     'password': 'bar'},
        properties={'num_cpu': 4},
        name='fake-node-1',
        extra={}
    ),
    stubs.StubIronicNode(
        id=3,
        uuid='33333333-4444-8888-9999-000000000000',
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
                     'password': 'bar'},
        properties={'memory_mb': 32768,
                    'cpu_arch': 'x86_64',
                    'local_gb': 120,
                    'cpus': 8,
                    'capabilities':
                        "server_hardware_type_uri:"
                        "/rest/server-hardware-types/1111112222233333,"
                        "enclosure_group_uri:"
                        "/rest/enclosure-groups/1111112222233333,"
                        "server_profile_template_uri:"
                        "/rest/server-profile-templates/1111112222233333"
                    },
        name='fake-node-1',
        extra={}
    )

]

STUB_ENCLOSURE_GROUP = stubs.StubEnclosureGroup(
    name='ENCLGROUP',
    uuid='22222222-TTTT-BBBB-9999-AAAAAAAAAAA',
    uri='/rest/server-hardware/22222222-TTTT-BBBB-9999-AAAAAAAAAAA',
)

STUB_SERVER_HARDWARE_TYPE = stubs.StubServerHardwareType(
    name='TYPETYPETYPE',
    uuid='22222222-7777-8888-9999-AAAAAAAAAAA',
    uri='/rest/server-hardware/22222222-7777-8888-9999-AAAAAAAAAAA',
)

POOL_OF_STUB_SERVER_HARDWARE = [
    stubs.StubServerHardware(
        name='AAAAA',
        uuid='11111111-7777-8888-9999-000000000000',
        uri='/rest/server-hardware/11111',
        power_state='Off',
        server_profile_uri='',
        server_hardware_type_uri='/rest/server-hardware-types/111112222233333',
        enclosure_group_uri='/rest/enclosure-groups/1111112222233333',
        status='OK',
        state='Unknown',
        state_reason='',
        enclosure_uri='/rest/enclosures/1111112222233333',
        processor_count=12,
        processor_core_count=12,
        memory_mb=16384,
        port_map=[],
        mp_host_info={}
    ),
    stubs.StubServerHardware(
        name='BBBBB',
        uuid='22222222-7777-8888-9999-000000000000',
        uri='/rest/server-hardware/22222',
        power_state='Off',
        server_profile_uri='',
        server_hardware_type_uri='/rest/server-hardware-types/111111222233333',
        enclosure_group_uri='/rest/enclosure-groups/1111112222233333',
        status='OK',
        state='Unknown',
        state_reason='',
        enclosure_uri='/rest/enclosures/1111112222233333',
        processor_count=12,
        processor_core_count=12,
        memory_mb=16384,
        port_map=[],
        mp_host_info={}
    ),
    stubs.StubServerHardware(
        name='CCCCC',
        uuid='33333333-7777-8888-9999-000000000000',
        uri='/rest/server-hardware/33333',
        power_state='Off',
        server_profile_uri='',
        server_hardware_type_uri='/rest/server-hardware-types/111111222223333',
        enclosure_group_uri='/rest/enclosure-groups/1111112222233333',
        status='OK',
        state='Unknown',
        state_reason='',
        enclosure_uri='/rest/enclosures/1111112222233333',
        processor_count=12,
        processor_core_count=12,
        memory_mb=16384,
        port_map=[],
        mp_host_info={}
    )
]


POOL_OF_STUB_SERVER_PROFILE_TEMPLATE = [
    stubs.StubServerProfileTemplate(
        uri='/rest/server-profile-templates/1111112222233333',
        name='TEMPLATETEMPLATETEMPLATE',
        server_hardware_type_uri='/rest/server-hardware-types/111112222233333',
        enclosure_group_uri='/rest/enclosure-groups/1111112222233333',
        connections=[],
        boot={}
    )
]


POOL_OF_STUB_NOVA_FLAVORS = [
    stubs.StubNovaFlavor(
        id=123,
        uuid='66666666-7777-8888-9999-000000000000',
        name='fake-flavor',
        memory_mb=1024,
        ram_mb=1024,
        vcpus=1,
        cpus=1,
        cpu_arch='x64',
        disk=100,
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


STUB_PARAMETERS = stubs.StubParameters(
    os_ironic_node_driver='fake_oneview',
    os_ironic_deploy_kernel_uuid='11111-22222-33333-44444-55555',
    os_ironic_deploy_ramdisk_uuid='55555-44444-33333-22222-11111'
)


@mock.patch('ironic_oneview_cli.facade.get_ironic_client')
@mock.patch('ironic_oneview_cli.common.client.ClientV2')
class FunctionalTestIronicOneviewCli(unittest.TestCase):

    def setUp(self):
        self.args = argparse.Namespace(
            ov_auth_url='https://my-oneview',
            ov_username='ov-user',
            ov_password='secret',
            ov_cacert='',
            os_auth_url='http://something',
            os_username='my_name',
            os_password='secret',
            os_project_name='my_tenant',
            os_tenant_name='my_tenant',
            insecure=True,
            os_cacert='',
            os_ironic_node_driver=STUB_PARAMETERS.os_ironic_node_driver,
            os_ironic_deploy_kernel_uuid=(
                STUB_PARAMETERS.os_ironic_deploy_kernel_uuid
            ),
            os_ironic_deploy_ramdisk_uuid=(
                STUB_PARAMETERS.os_ironic_deploy_ramdisk_uuid
            )
        )

    @mock.patch('ironic_oneview_cli.create_node_shell.commands.input')
    def test_node_creation(self, mock_input,
                           mock_oneview_client, mock_ironic_client):
        oneview_client = mock_oneview_client.return_value
        oneview_client.server_hardware.list.return_value = (
            POOL_OF_STUB_SERVER_HARDWARE
        )
        oneview_client.server_profile_template.list.return_value = (
            POOL_OF_STUB_SERVER_PROFILE_TEMPLATE
        )
        spt_index = 0
        sh_index = 0
        mock_input.side_effect = [
            str(spt_index + 1),
            str(sh_index + 1),
            'n'
        ]

        create_node_cmd.do_node_create(self.args)

        selected_sh = POOL_OF_STUB_SERVER_HARDWARE[sh_index]
        selected_spt = POOL_OF_STUB_SERVER_PROFILE_TEMPLATE[spt_index]
        attrs = {
            'driver': STUB_PARAMETERS.os_ironic_node_driver,
            'driver_info': {
                'dynamic_allocation': True,
                'deploy_kernel': STUB_PARAMETERS.os_ironic_deploy_kernel_uuid,
                'deploy_ramdisk':
                    STUB_PARAMETERS.os_ironic_deploy_ramdisk_uuid,
                'server_hardware_uri':
                    selected_sh.uri,
            },
            'properties': {
                'cpus': selected_sh.cpus,
                'memory_mb': selected_sh.memory_mb,
                'local_gb': selected_sh.local_gb,
                'cpu_arch': selected_sh.cpu_arch,
                'capabilities':
                    'server_hardware_type_uri:%s,'
                    'enclosure_group_uri:%s,'
                    'server_profile_template_uri:%s' % (
                        selected_sh.server_hardware_type_uri,
                        selected_sh.enclosure_group_uri,
                        selected_spt.uri
                    )
            }
        }

        ironic_client = mock_ironic_client.return_value
        ironic_client.node.create.assert_called_with(
            **attrs
        )

    @mock.patch('ironic_oneview_cli.create_flavor_shell.commands.input')
    @mock.patch('ironic_oneview_cli.facade.get_nova_client')
    def test_flavor_creation(self, mock_nova_client, mock_input,
                             mock_oneview_client, mock_ironic_client,):
        ironic_client = mock_ironic_client.return_value
        ironic_client.node.list.return_value = (
            POOL_OF_STUB_IRONIC_NODES
        )

        # Nodes 0 and 1 doesn't have the required attributes, will not be shown
        node_selected = POOL_OF_STUB_IRONIC_NODES[2]
        flavor_name = 'my-flavor'
        mock_input.side_effect = ['1', flavor_name, 'n']
        create_flavor_cmd.do_flavor_create(self.args)

        attrs = {
            'name': flavor_name,
            'ram': node_selected.properties.get('memory_mb'),
            'vcpus': node_selected.properties.get('cpus'),
            'disk': node_selected.properties.get('local_gb')
        }

        nova_client = mock_nova_client.return_value
        nova_client.flavors.create.assert_called_with(
            **attrs
        )


if __name__ == '__main__':
    unittest.main()
