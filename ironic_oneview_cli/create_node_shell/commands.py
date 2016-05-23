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

import sys

from builtins import input

from ironic_oneview_cli.facade import Facade
from ironic_oneview_cli.objects import ServerHardwareManager
from ironic_oneview_cli.objects import ServerProfileManager
from ironic_oneview_cli.openstack.common import cliutils


# NOTE(thiagop): is this a facade too?
class NodeCreator(object):

    def __init__(self, facade):
        self.facade = facade

    def print_prompt(self, object_list, header_list, mixed_case_list,
                     input_message, field_labels=None):
        cliutils.print_list(object_list, header_list,
                            mixed_case_fields=mixed_case_list,
                            field_labels=field_labels)
        input_value = input(input_message)
        return input_value

    def is_entry_invalid(self, entries, objects_list):
        for entry in entries:
            element = self.get_element_by_id(objects_list, entry)
            if element is None:
                return True
        return False

    def get_element_by_id(self, element_list, element_id):
        try:
            for element in element_list:
                if element.id == int(element_id):
                    return element
        except Exception:
            return None

    def assign_elements_with_new_id(self, element_list):
        counter = 1
        for element in element_list:
            element.id = counter
            counter += 1

    def list_server_hardware_not_enrolled(self, server_hardware_objects):
        nodes_server_hardware_uris = []
        nodes = filter(lambda x: x.driver.endswith("_oneview"),
                       self.facade.get_ironic_node_list())
        for node in nodes:
            node_server_hardware_uri = node.driver_info.get(
                'server_hardware_uri'
            )
            if node_server_hardware_uri is not None:
                nodes_server_hardware_uris.append(node_server_hardware_uri)
        server_hardware_objects_not_created = []
        for server_hardware in server_hardware_objects:
            if server_hardware.uri not in nodes_server_hardware_uris:
                server_hardware_objects_not_created.append(server_hardware)
        return server_hardware_objects_not_created

    def select_server_profile_template(self, server_profile_list):
        server_profile_selected = None
        self.assign_elements_with_new_id(server_profile_list)
        while server_profile_selected is None:
            input_id = self.print_prompt(
                server_profile_list,
                ['id', 'name', 'enclosureGroupName', 'serverHardwareTypeName'],
                ['enclosureGroupName', 'serverHardwareTypeName'],
                "Enter the id of the Server Profile Template you want to use. "
                "('q' to quit)> ",
                field_labels=[
                    'Id',
                    'Name',
                    'Enclosure Group Name',
                    'Server Hardware Type Name'
                ]
            )
            if input_id == 'q':
                sys.exit()
            server_profile_selected = self.get_element_by_id(
                server_profile_list, input_id)

        print("\nYou choose the following Server Profile Template: ")
        cliutils.print_list(
            [server_profile_selected],
            ['name', 'enclosureGroupName', 'serverHardwareTypeName'],
            mixed_case_fields=['enclosureGroupName', 'serverHardwareTypeName'],
            field_labels=[
                'Name',
                'Enclosure Group Name',
                'Server Hardware Type Name'
            ]
        )

        return server_profile_selected

    def select_server_hardware_objects(self, server_hardware_list):
        invalid_server_hardwares = True
        self.assign_elements_with_new_id(server_hardware_list)
        while invalid_server_hardwares:
            input_id = self.print_prompt(
                server_hardware_list,
                ['id',
                 'name',
                 'cpus',
                 'memoryMb',
                 'local_gb',
                 'serverGroupName',
                 'serverHardwareTypeName'
                 ],
                ['serverHardwareTypeUri',
                 'memoryMb',
                 'serverGroupUri',
                 'processorCoreCount',
                 'processorCount',
                 'serverHardwareTypeName',
                 'serverGroupName'
                 ],
                "Enter a space separated list of Server Hardware ids you want "
                "to use, e.g. 1 2 3 4. ('q' to quit)> ",
                field_labels=[
                    'Id',
                    'Name',
                    'CPUs',
                    'Memory MB',
                    'Disk GB',
                    'Enclosure Group Name',
                    'Server Hardware Type Name'
                ]
            )
            if input_id == 'q':
                sys.exit()
            server_hardware_ids_selected = input_id.split()
            invalid_server_hardwares = self.is_entry_invalid(
                server_hardware_ids_selected, server_hardware_list)

        return server_hardware_ids_selected

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
                'cpus': server_hardware.cpus,
                'memory_mb': server_hardware.memoryMb,
                'local_gb': server_hardware.local_gb,
                'cpu_arch': server_hardware.cpu_arch,
                'capabilities': 'server_hardware_type_uri:%s,'
                                'enclosure_group_uri:%s,'
                                'server_profile_template_uri:%s' % (
                                    server_hardware.serverHardwareTypeUri,
                                    server_hardware.serverGroupUri,
                                    server_profile_template.uri,
                                )
            }
        }

        node = None
        try:
            node = self.facade.create_ironic_node(**attrs)
        except Exception as e:
            print(e.message)

        return node


@cliutils.arg('--detail', dest='detail', action='store_true', default=False,
              help="Show detailed information about the nodes.")
def do_node_create(args):
    """Creates nodes based on available HP OneView Server Hardware."""

    node_creator = NodeCreator(Facade(args))
    hardware_manager = ServerHardwareManager(args)
    profile_manager = ServerProfileManager(args)

    print("Retrieving Server Profile Templates from OneView...")
    available_hardware = node_creator.list_server_hardware_not_enrolled(
        hardware_manager.list(only_available=True)
    )
    # FIXME(thiagop): doesn't uses facade or node_creator
    template_list = profile_manager.list_templates_compatible_with(
        available_hardware
    )

    create_another_node_flag = True
    while create_another_node_flag:
        create_another_node_flag = False

        template_selected = node_creator.select_server_profile_template(
            template_list
        )
        print('\nListing compatible Server Hardware objects...')

        # FIXME(thiagop): doesn't uses facade or node_creator
        available_server_hardware_by_field = hardware_manager.list(
            only_available=True,
            fields={
                'serverHardwareTypeUri':
                    template_selected.serverHardwareTypeUri,
                'serverGroupUri':
                    template_selected.enclosureGroupUri
            }
        )

        server_hardware_list = node_creator.list_server_hardware_not_enrolled(
            available_server_hardware_by_field
        )
        server_hardware_ids_selected = node_creator.select_server_hardware_objects(
            server_hardware_list
        )
        for server_hardware_id in server_hardware_ids_selected:
            server_hardware_selected = node_creator.get_element_by_id(
                server_hardware_list, server_hardware_id)
            print('\nCreating a Node to represent the following Server '
                  'Hardware...')
            cliutils.print_list(
                [server_hardware_selected],
                ['name', 'cpus', 'memoryMb', 'local_gb', 'serverGroupName',
                 'serverHardwareTypeName'],
                mixed_case_fields=[
                    'serverGroupName',
                    'memoryMb',
                    'serverHardwareTypeName'
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

            node = node_creator.create_node(
                args, server_hardware_selected, template_selected
            )

            if node:
                print('Node created!\n')

        while True:
            response = input('Would you like to create another Node? [Y/n] ')
            if response == 'n':
                create_another_node_flag = False
                break
            elif response.lower() == 'y' or not response:
                create_another_node_flag = True
                break
            else:
                print('Invalid option')
