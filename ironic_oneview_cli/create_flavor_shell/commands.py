# Copyright (2015-2017) Hewlett Packard Enterprise Development LP
# Copyright (2015-2017) Universidade Federal de Campina Grande
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

import re

from ironic_oneview_cli import common
from ironic_oneview_cli.create_flavor_shell import objects
from ironic_oneview_cli import facade
from ironic_oneview_cli import service_logging as logging

LOG = logging.getLogger(__name__)


class FlavorCreator(object):

    def __init__(self, facade_obj):
        self.facade = facade_obj

    def get_oneview_nodes(self):
        return common.get_oneview_nodes(self.facade.get_ironic_node_list())

    def get_flavor_from_ironic_node(self, flavor_id, node):
        server_hardware_uri = node.driver_info.get("server_hardware_uri")
        server_hardware = self.facade.get_server_hardware(server_hardware_uri)

        server_hardware_type = self.facade.get_server_hardware_type(
            server_hardware.get("serverHardwareTypeUri")
        )

        enclosure_group = self.facade.get_enclosure_group(
            server_hardware.get("serverGroupUri")
        )

        capabilities = node.properties.get("capabilities")
        match = re.search(
            r"server_profile_template_uri:(?P<uri>[a-zA-Z0-9\-\/]+)",
            capabilities
        )
        server_profile_template_uri = match.group('uri')
        server_profile_template = self.facade.get_server_profile_template(
            server_profile_template_uri
        )

        flavor = self.set_flavor_properties(
            node, server_hardware_type,
            enclosure_group, server_profile_template
        )

        return objects.Flavor(flavor_id=flavor_id, info=flavor)

    @staticmethod
    def set_flavor_properties(node, server_hardware_type,
                              enclosure_group, server_profile_template):
        flavor = {}

        flavor['ram_mb'] = node.properties.get('memory_mb')
        flavor['cpus'] = node.properties.get('cpus')
        flavor['disk'] = node.properties.get('local_gb')
        flavor['cpu_arch'] = node.properties.get('cpu_arch')
        flavor['server_hardware_type_name'] = (
            common.get_attribute_from_dict(server_hardware_type, 'name'))
        flavor['server_hardware_type_uri'] = (
            common.get_attribute_from_dict(server_hardware_type, 'uri'))
        flavor['enclosure_group_name'] = (
            common.get_attribute_from_dict(enclosure_group, 'name'))
        flavor['enclosure_group_uri'] = (
            common.get_attribute_from_dict(enclosure_group, 'uri'))
        flavor['server_profile_template_name'] = (
            common.get_attribute_from_dict(server_profile_template, 'name'))
        flavor['server_profile_template_uri'] = (
            common.get_attribute_from_dict(server_profile_template, 'uri'))

        return flavor

    def get_flavor_list(self, nodes):
        flavors = []

        id_counter = 1
        for node in nodes:
            if node.properties.get('memory_mb'):
                flavors.append(
                    self.get_flavor_from_ironic_node(id_counter, node)
                )
                id_counter += 1
        return sorted(set(flavors), key=lambda x: x.cpus)

    def create_flavor(self, flavor_name, flavor):
        attrs = {
            'name': flavor_name,
            'ram': flavor.get('ram_mb'),
            'vcpus': flavor.get('cpus'),
            'disk': flavor.get('disk')
        }
        extra_specs = flavor.get("flavor_obj").extra_specs()

        try:
            flavor = self.facade.create_nova_flavor(**attrs)
            flavor.set_keys(extra_specs)
        except Exception as e:
            raise e

        print("Flavor %s was created." % flavor.name)


@common.arg(
    '--node',
    metavar='<node>',
    help='A Ironic node to create the flavor for.')
@common.arg(
    '--name',
    metavar='<name>',
    help='The name of the flavor to be created.')
def do_flavor_create(args):
    """Create flavors based on available Ironic nodes.

    Shows a list with suggested Flavors to be created based on OneView's Server
    Profile Templates. The user can then select a Flavor to create based on
    it's ID.
    """
    cli_facade = facade.Facade(args)
    flavor_creator = FlavorCreator(cli_facade)
    nodes = flavor_creator.get_oneview_nodes()

    if args.name and not args.node:
        print("It is mandatory to specify an Ironic Node for flavor creation. "
              "Use --node")
        return
    elif not nodes:
        print("No Ironic nodes running OneView drivers were found. "
              "Please, create a node to be used as base for the flavor.")
        return

    LOG.info("Retrieving possible configurations for flavor creation...")
    if args.node:
        nodes = [common.get_element(nodes, args.node)]
        if nodes[0] is None:
            print("Could not find an Ironic Node matching '%s'"
                  % args.node)
            return

    flavor_list = flavor_creator.get_flavor_list(nodes)

    flavor_dict_list = []
    for flavor in flavor_list:
        flavor_dict_list.append(flavor.__dict__)
        flavor_dict_list[-1]["flavor_obj"] = flavor

    common.assign_elements_with_new_id(flavor_dict_list)

    if not args.node:
        _interactive_flavor(flavor_creator, flavor_dict_list)
    else:
        flavor = flavor_dict_list[0]
        flavor_name = args.name or common.generate_template_flavor_name(flavor)
        _create_flavor(flavor_creator, flavor, flavor_name)


def _interactive_flavor(flavor_creator, flavor_dict_list):
    while True:
        input_id = common.print_prompt(
            flavor_dict_list,
            [
                'id',
                'cpus',
                'disk',
                'ram_mb',
                'server_profile_template_name',
                'server_hardware_type_name',
                'enclosure_group_name'
            ],
            "Insert Flavor ID to add in OneView. Press 'q' to quit> ",
            [
                'Id',
                'CPUs',
                'Disk GB',
                'Memory MB',
                'Server Profile Template',
                'Server Hardware Type',
                'Enclosure Group Name'
            ],
        )
        if input_id == "q":
            break

        invalid_entry_id = common.is_entry_invalid(input_id, flavor_dict_list)
        if invalid_entry_id:
            print('Invalid Flavor ID. Please enter a valid ID.')
            continue

        flavor = common.get_element_by_id(flavor_dict_list, input_id)

        _create_flavor(flavor_creator, flavor)

        message = 'Would you like to create another Flavor(s)? [y/N] '
        response = common.approve_command_prompt(message)
        if not response:
            break


def _create_flavor(flavor_creator, flavor, flavor_name=None):
    print("Listing chosen flavor configuration...")
    common.print_prompt(
        [flavor],
        [
            'cpus',
            'disk',
            'ram_mb',
            'server_profile_template_name',
            'server_hardware_type_name',
            'enclosure_group_name'
        ],
        field_labels=[
            'CPUs',
            'Local GB',
            'Memory MB',
            'Server Profile Template',
            'Server Hardware Type',
            'Enclosure Group Name'
        ]
    )
    flavor_name = flavor_name or common.set_flavor_name(flavor)
    flavor_creator.create_flavor(flavor_name, flavor)
