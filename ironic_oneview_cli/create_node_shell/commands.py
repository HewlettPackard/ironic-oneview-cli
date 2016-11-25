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

import sys

from ironic_oneview_cli import common
from ironic_oneview_cli import facade


class NodeCreator(object):
    def __init__(self, facade):
        self.facade = facade

    def is_server_profile_applied(self, server_hardware):
        return server_hardware.server_profile_uri not in (None, '')

    def is_enrolled_on_ironic(self, server_hardware):
        nodes = filter(lambda x: x.driver in common.SUPPORTED_DRIVERS,
                       self.facade.get_ironic_node_list())
        for node in nodes:
            sh_uri = node.driver_info.get(
                'server_hardware_uri'
            )
            if sh_uri not in(None, '') and sh_uri == server_hardware.uri:
                return True
        return False

    def list_server_hardware(self):
        return self.facade.list_server_hardware_available()

    def filter_server_hardware(self, **kwargs):
        server_hardware_objects = self.facade.filter_server_hardware_available(
            **kwargs
        )
        for server_hardware in server_hardware_objects:
            # Here comes the infamous HACK of local_gb and cpu_arch
            # NOTE(nicodemos): Used only if os_inspection_enabled = False
            server_hardware.local_gb = 120
            server_hardware.cpu_arch = 'x86_64'

            enclosure_group = self.facade.get_enclosure_group(
                server_hardware.enclosure_group_uri
            )
            if enclosure_group:
                server_hardware.enclosure_group_name = enclosure_group.name
            server_hardware_type = self.facade.get_server_hardware_type(
                server_hardware.server_hardware_type_uri
            )
            if server_hardware_type:
                server_hardware.server_hardware_type_name = (
                    server_hardware_type.name
                )
            is_enrolled = self.is_enrolled_on_ironic(server_hardware)
            setattr(server_hardware, "enrolled", is_enrolled)

        return server_hardware_objects

    def get_templates_compatible_with(self, server_hardware_objects):
        spt_list = self.facade.list_templates_compatible_with(
            server_hardware_objects
        )
        for spt in spt_list:
            enclosure_group = self.facade.get_enclosure_group(
                spt.enclosure_group_uri
            )
            if enclosure_group:
                spt.enclosure_group_name = enclosure_group.name
            server_hardware_type = self.facade.get_server_hardware_type(
                spt.server_hardware_type_uri
            )
            if server_hardware_type:
                spt.server_hardware_type_name = server_hardware_type.name

        return sorted(spt_list, key=lambda x: x.name.lower())

    def get_server_hardware_list(self, server_profile_template):
        selected_sht_uri = server_profile_template.server_hardware_type_uri
        selected_eg_uri = server_profile_template.enclosure_group_uri

        server_hardware_list = self.filter_server_hardware(
            server_hardware_type_uri=selected_sht_uri,
            enclosure_group_uri=selected_eg_uri
        )

        return sorted(server_hardware_list, key=lambda x: x.name.lower())

    def create_node(self, args, server_hardware, server_profile_template):
        attrs = {
            # TODO(thiagop): turn 'name' into a valid server name
            # 'name': server_hardware.name,
            'driver': args.os_ironic_node_driver,
            'driver_info': {
                'deploy_kernel': args.os_ironic_deploy_kernel_uuid,
                'deploy_ramdisk': args.os_ironic_deploy_ramdisk_uuid,
                'server_hardware_uri': server_hardware.uri,
                # NOTE (liliars): flag to turn on dynamic allocation for
                # every new node
                # NOTE(caiobo): the flag should be removed once the
                # support for pre-allocation is dropped.
                'dynamic_allocation': True,
            },
            'properties': {
                'capabilities': 'server_hardware_type_uri:%s,'
                                'enclosure_group_uri:%s,'
                                'server_profile_template_uri:%s' % (
                                    server_hardware.server_hardware_type_uri,
                                    server_hardware.enclosure_group_uri,
                                    server_profile_template.uri,
                                )
            }
        }

        if not args.os_inspection_enabled:
            hardware_properties = {
                'cpus': server_hardware.cpus,
                'memory_mb': server_hardware.memory_mb,
                'local_gb': server_hardware.local_gb,
                'cpu_arch': server_hardware.cpu_arch
            }

            attrs['properties'].update(hardware_properties)

        try:
            self.facade.create_ironic_node(**attrs)
        except Exception as e:
            raise e


@common.arg(
    '-n', '--number',
    metavar='<number>',
    type=int,
    help='Create n nodes based on a given HP OneView Server Profile Template.')
@common.arg(
    '-spt', '--server-profile-template-name',
    metavar='<spt_name>',
    default=None,
    help='Name of the HP OneView Server Profile Template.')
def do_node_create(args):
    """Creates nodes based on available HP OneView Objects."""

    node_creator = NodeCreator(facade.Facade(args))

    spt_list = node_creator.get_templates_compatible_with(
        node_creator.list_server_hardware()
    )
    common.assign_elements_with_new_id(spt_list)

    template_selected = common.get_element_by_name(
        spt_list, args.server_profile_template_name
    )

    while template_selected is None:
        input_id = common.print_prompt(
            spt_list,
            [
                'id',
                'name',
                'enclosure_group_name',
                'server_hardware_type_name'
            ],
            "Enter the id of the Server Profile Template you want to "
            "use (Press 'q' to quit)> ",
            [
                'Id',
                'Name',
                'Enclosure Group Name',
                'Server Hardware Type Name'
            ]
        )
        if input_id == 'q':
            sys.exit()

        template_selected = common.get_element_by_id(
            spt_list, input_id
        )

    print("\nYou choose the following Server Profile Template: ")
    common.print_prompt(
        [template_selected],
        [
            'name',
            'enclosure_group_name',
            'server_hardware_type_name'
        ],
        field_labels=[
            'Name',
            'Enclosure Group Name',
            'Server Hardware Type Name'
        ]
    )

    s_hardware_list = node_creator.get_server_hardware_list(
        template_selected
    )

    common.assign_elements_with_new_id(s_hardware_list)

    if args.number:
        print(("Creating %(number_of_nodes)s nodes with the specific "
               "Server Hardware") % {'number_of_nodes': args.number})
        common.print_prompt(
            [s_hardware_list[0]],
            [
                'cpus',
                'memory_mb',
                'local_gb',
                'cpu_arch',
                'enclosure_group_name',
                'server_hardware_type_name'
            ],
            field_labels=[
                'CPUs',
                'Memory MB',
                'Disk GB',
                'CPU Arch',
                'Enclosure Group Name',
                'Server Hardware Type Name'
            ]
        )

        for node_index in range(args.number):
            node = common.get_element_by_id(
                s_hardware_list,
                str(node_index + 1)
            )
            if (node is None):
                print(("Only %(node_index)s nodes created") %
                      {'node_index': node_index})
                break
            else:
                node_creator.create_node(
                    args, node, template_selected
                )

        print('\nNodes created!')

    else:
        print('\nListing compatible Server Hardware objects...')

        invalid_server_hardwares = True
        while invalid_server_hardwares:
            input_id = common.print_prompt(
                s_hardware_list,
                [
                    'id',
                    'name',
                    'cpus',
                    'memory_mb',
                    'local_gb',
                    'cpu_arch',
                    'enclosure_group_name',
                    'server_hardware_type_name',
                    'enrolled'
                ],
                "Enter a space separated list of Server Hardware "
                "ids you want to use, e.g. 1 2 3 4. ('q' to quit)> ",
                field_labels=[
                    'Id',
                    'Name',
                    'CPUs',
                    'Memory MB',
                    'Disk GB',
                    'CPU Arch',
                    'Enclosure Group Name',
                    'Server Hardware Type Name',
                    'Enrolled'
                ]
            )
            if input_id == 'q':
                sys.exit()

            s_hardware_ids_selected = input_id.split()
            invalid_server_hardwares = common.is_entry_invalid(
                s_hardware_ids_selected, s_hardware_list)

        for server_hardware_id in s_hardware_ids_selected:
            server_hardware_selected = common.get_element_by_id(
                s_hardware_list,
                server_hardware_id
            )
            print('\n')
            if not node_creator.is_enrolled_on_ironic(
                    server_hardware_selected):
                print(
                    'Creating a node to represent the following Server'
                    'Hardware..'
                )
                common.print_prompt(
                    [server_hardware_selected],
                    [
                        'name',
                        'cpus',
                        'memory_mb',
                        'local_gb',
                        'enclosure_group_name',
                        'server_hardware_type_name'
                    ],
                    field_labels=[
                        'Name',
                        'CPUs',
                        'Memory MB',
                        'Local GB',
                        'Server Group Name',
                        'Server Hardware Type Name'
                    ]
                )
                if node_creator.is_server_profile_applied(
                    server_hardware_selected
                ):
                    print('Warning: This Server Hardware '
                          'is in use by OneView.')

                node_creator.create_node(
                    args, server_hardware_selected, template_selected
                )

                print('Node created!')
            else:
                print('ERROR: It was not possible create the node, this Server'
                      ' Hardware is enrolled on Ironic.')
