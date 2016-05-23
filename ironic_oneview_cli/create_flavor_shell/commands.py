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

from builtins import input

from ironic_oneview_cli.create_flavor_shell import objects
from ironic_oneview_cli import facade
from ironic_oneview_cli import objects as cli_objects
from ironic_oneview_cli.openstack.common import cliutils


class FlavorCreator(object):

    def __init__(self, facade):
        self.facade = facade

    def get_flavor_name(self, flavor):
        FLAVOR_NAME_TEMPLATE = "%sMB-RAM_%s_%s_%s"
        return FLAVOR_NAME_TEMPLATE % (
            flavor.ram_mb,
            flavor.cpus,
            flavor.cpu_arch,
            flavor.disk)

    def get_element_by_id(self, element_list, element_id):
        for element in element_list:
            if element.id == element_id:
                return element

    def get_flavor_from_ironic_node(self, flavor_id, node, hardware_manager,
                                    profile_manager):
        flavor = {}

        flavor['ram_mb'] = node.properties.get("memory_mb")
        flavor['cpus'] = node.properties.get("cpus")
        flavor['disk'] = node.properties.get("local_gb")
        flavor['cpu_arch'] = 'x86_64'

        capabilities = node.properties.get("capabilities")

        if capabilities is not None:
            capabilities = capabilities.split(",")

            for field in capabilities:
                data = field.split(":")
                if data[0] == 'server_hardware_type_uri':
                    flavor['server_hardware_type_uri'] = data[1]
                elif data[0] == 'enclosure_group_uri':
                    flavor['enclosure_group_uri'] = data[1]
                elif data[0] == 'server_profile_template_uri':
                    flavor['server_profile_template_uri'] = data[1]

            available_server_hardware_by_field = hardware_manager.list(
                only_available=True,
                fields={
                    'serverHardwareTypeUri':
                    flavor['server_hardware_type_uri'],
                    'serverGroupUri':
                    flavor['enclosure_group_uri'],
                    'serverProfileUri':
                    flavor['server_profile_template_uri'],
                    'uri':
                    node.driver_info.get('server_hardware_uri')
                }
            )

            template_list = profile_manager.list_templates_compatible_with(
                available_server_hardware_by_field
            )

            for available in available_server_hardware_by_field:
                flavor['server_hardware_type_name'] = available.serverHardwareTypeName
                flavor['enclosure_group_name'] = available.serverGroupName

            for available in template_list:
                flavor['server_profile_template_name'] = available.name

        return objects.Flavor(id=flavor_id, info=flavor)

    def get_flavor_list(self, hardware_manager, profile_manager):
        nodes = self.facade.get_ironic_node_list()
        flavors = []

        id_counter = 1
        for node in nodes:
            if node.properties.get('memory_mb') is not None:
                flavors.append(
                    self.get_flavor_from_ironic_node(
                        id_counter, node, hardware_manager, profile_manager
                    )
                )
                id_counter += 1

        return set(flavors)

    def create_flavor(self, name, ram, vcpus, disk, extra_specs={}):
        attrs = {
            'name': name,
            'ram': ram,
            'vcpus': vcpus,
            'disk': disk
        }

        flavor = None
        try:
            flavor = self.facade.create_nova_flavor(**attrs)
            flavor.set_keys(extra_specs)
        except Exception as e:
            print(e.message)

        return flavor


def do_flavor_create(args):
    """Creates flavors based on available Ironic nodes.

    Shows a list with suggested Flavors to be created based on OneView's Server
    Profile Templates. The user can then select a Flavor to create based on
    it's ID.
    """

    cli_facade = facade.Facade(args)
    nodes = len(cli_facade.get_ironic_node_list())

    if not nodes:
        print("No Ironic nodes were found. Please, create a node to be used as base for the Flavor.")
        return

    flavor_creator = FlavorCreator(cli_facade)
    hardware_manager = cli_objects.ServerHardwareManager(args)
    profile_manager = cli_objects.ServerProfileManager(args)

    print("Retrieving possible configurations for Flavor creation...")

    flavor_list = flavor_creator.get_flavor_list(hardware_manager, profile_manager)
    flavor_list = list(flavor_list)
    for j in range(1, len(flavor_list)):
        key = flavor_list[j]
        i = j - 1
        while i >= 0 and int(flavor_list[i].cpus) > int(key.cpus):
            flavor_list[i + 1] = flavor_list[i]
            i -= 1
        flavor_list[i + 1] = key

    for i in range(0, len(flavor_list)):
        flavor_list[i].__setitem__(i + 1)

    flavor_list = set(flavor_list)

    create_another_flavor_flag = True
    while create_another_flavor_flag:
        create_another_flavor_flag = False
        cliutils.print_list(
            flavor_list,
            ['id', 'cpus', 'disk', 'ram_mb', 'server_profile_template_name',
             'server_hardware_type_name', 'enclosure_group_name'],
            field_labels=['Id', 'CPUs', 'Disk GB', 'Memory MB',
                          'Server Profile Template', 'Server Hardware Type',
                          'Enclosure Group Name'],
            sortby_index=1)
        id = input("Insert Flavor ID to add in OneView. Press 'q' to quit> ")

        if id == "q":
            break

        if id.isdigit() is not True:
            print('Invalid Flavor ID. Please enter a valid ID.')
            create_another_flavor_flag = True
            continue

        flavor = flavor_creator.get_element_by_id(flavor_list, int(id))

        if flavor is None:
            print('Invalid Flavor ID. Please enter a valid ID.')
            create_another_flavor_flag = True
            continue

        print("Listing chosen Flavor configuration...")

        cliutils.print_list(
            [flavor],
            ['cpus', 'disk', 'ram_mb', 'server_profile_template_name',
             'server_hardware_type_name', 'enclosure_group_name'],
            field_labels=['CPUs', 'Disk GB', 'Memory MB',
                          'Server Profile Template', 'Server Hardware Type',
                          'Enclosure Group Name'],
            sortby_index=2)
        flavor_name_default = flavor_creator.get_flavor_name(flavor)
        flavor_name = input(
            "Insert a name for the Flavor [" +
            flavor_name_default + "] (press 'q' to quit)> ")

        if flavor_name == "q":
            break

        if len(flavor_name) == 0:
            flavor_name = flavor_name_default

        flavor = flavor_creator.create_flavor(
            flavor_name,
            flavor.ram_mb,
            flavor.cpus,
            flavor.disk,
            flavor.extra_specs()
        )

        if flavor:
            print('Flavor created!\n')

        while True:
            response = input('Would you like to create another Flavor? [Y/n] ')
            if response == 'n':
                create_another_flavor_flag = False
                break
            elif response.lower() == 'y' or not response:
                create_another_flavor_flag = True
                break
            else:
                print('Invalid option')
