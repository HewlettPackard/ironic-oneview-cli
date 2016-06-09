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

from ironic_oneview_cli import common
from ironic_oneview_cli import facade
from ironic_oneview_cli.openstack.common import cliutils


class NodeCreator(object):

    def __init__(self, facade):
        self.facade = facade

    def filter_not_enrolled_on_ironic(self, server_hardware_objects):
        nodes_server_hardware_uris = []
        nodes = filter(lambda x: x.driver in common.SUPPORTED_DRIVERS,
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

    def list_server_hardware_not_enrolled(self):
        server_hardware_objects = self.facade.list_server_hardware_available()
        sh_not_enrolled = self.filter_not_enrolled_on_ironic(
            server_hardware_objects
        )
        return sh_not_enrolled

    def filter_server_hardware_not_enrolled(self, **kwargs):
        server_hardware_objects = self.facade.filter_server_hardware_available(
            **kwargs
        )
        sh_not_enrolled = self.filter_not_enrolled_on_ironic(
            server_hardware_objects
        )

        for sh in sh_not_enrolled:
            enclosure_group = self.facade.get_enclosure_group(
                sh.enclosure_group_uri
            )
            if enclosure_group:
                sh.enclosure_group_name = enclosure_group.name
            server_hardware_type = self.facade.get_server_hardware_type(
                sh.server_hardware_type_uri
            )
            if server_hardware_type:
                sh.server_hardware_type_name = server_hardware_type.name

        return sh_not_enrolled

    def filter_templates_compatible_with(self, available_hardware):
        spt_list = self.facade.list_templates_compatible_with(
            available_hardware
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

        return spt_list

    def create_node(self, args, server_hardware, server_profile_template):
        # Here comes the infamous HACK of local_gb and cpu_arch
        server_hardware.local_gb = 120
        server_hardware.cpu_arch = 'x86_64'

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
                'memory_mb': server_hardware.memory_mb,
                'local_gb': server_hardware.local_gb,
                'cpu_arch': server_hardware.cpu_arch,
                'capabilities': 'server_hardware_type_uri:%s,'
                                'enclosure_group_uri:%s,'
                                'server_profile_template_uri:%s' % (
                                    server_hardware.server_hardware_type_uri,
                                    server_hardware.enclosure_group_uri,
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


def print_prompt(object_list, header_list, input_message=None,
                 field_labels=None):
    cliutils.print_list(
        object_list,
        header_list,
        mixed_case_fields=[],
        field_labels=field_labels
    )
    if input_message is not None:
        input_value = input(input_message)
        return input_value


def assign_elements_with_new_id(element_list):
    counter = 1
    for element in element_list:
        element.id = counter
        counter += 1


def get_element_by_id(element_list, element_id):
    try:
        for element in element_list:
            if element.id == int(element_id):
                return element
    except Exception:
        return None


def is_entry_invalid(entries, objects_list):
    for entry in entries:
        element = get_element_by_id(objects_list, entry)
        if element is None:
            return True
    return False


def do_node_create(args):
    """Creates nodes based on available HP OneView Server Hardware."""

    node_creator = NodeCreator(facade.Facade(args))

    print("Retrieving Server Profile Templates from OneView...")
    available_hardware = node_creator.list_server_hardware_not_enrolled()

    create_another_node_flag = True
    while create_another_node_flag:
        create_another_node_flag = False

        spt_list = node_creator.filter_templates_compatible_with(
            available_hardware
        )

        assign_elements_with_new_id(spt_list)

        template_selected = None
        while template_selected is None:
            input_id = print_prompt(
                spt_list,
                [
                    'id',
                    'name',
                    'enclosure_group_name',
                    'server_hardware_type_name'
                ],
                input_message="Enter the id of the Server Profile Template "
                "you want to use. (Press 'q' to quit)> ",
                field_labels=[
                    'Id',
                    'Name',
                    'Enclosure Group Name',
                    'Server Hardware Type Name'
                ]
            )
            if input_id == 'q':
                sys.exit()
            template_selected = get_element_by_id(
                spt_list, input_id
            )

        print("\nYou choose the following Server Profile Template: ")
        print_prompt(
            [template_selected],
            ['name', 'enclosure_group_name', 'server_hardware_type_name'],
            field_labels=[
                'Name',
                'Enclosure Group Name',
                'Server Hardware Type Name'
            ]
        )

        print('\nListing compatible Server Hardware objects...')
        selected_sht_uri = template_selected.server_hardware_type_uri
        selected_eg_uri = template_selected.enclosure_group_uri
        s_hardware_list = node_creator.filter_server_hardware_not_enrolled(
            server_hardware_type_uri=selected_sht_uri,
            enclosure_group_uri=selected_eg_uri
        )

        assign_elements_with_new_id(s_hardware_list)

        invalid_server_hardwares = True
        while invalid_server_hardwares:
            input_id = print_prompt(
                s_hardware_list,
                ['id',
                 'name',
                 'cpus',
                 'memory_mb',
                 'local_gb',
                 'enclosure_group_name',
                 'server_hardware_type_name'
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
            s_hardware_ids_selected = input_id.split()
            invalid_server_hardwares = is_entry_invalid(
                s_hardware_ids_selected, s_hardware_list)

        for server_hardware_id in s_hardware_ids_selected:
            server_hardware_selected = get_element_by_id(s_hardware_list,
                                                         server_hardware_id)
            print('\nCreating a node to represent the following Server' +
                  ' Hardware..')
            print_prompt(
                object_list=[server_hardware_selected],
                header_list=[
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
