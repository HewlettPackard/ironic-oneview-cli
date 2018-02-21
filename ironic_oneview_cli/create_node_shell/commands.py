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

import sys

from ironic_oneview_cli import common
from ironic_oneview_cli.create_port_shell import commands as port_cmd
from ironic_oneview_cli import facade


class NodeCreator(object):
    def __init__(self, facade_obj):
        self.facade = facade_obj

    def get_oneview_nodes(self):
        return common.get_oneview_nodes(self.facade.get_ironic_node_list())

    @staticmethod
    def is_server_profile_applied(server_hardware):
        return bool(server_hardware.get('serverProfileUri'))

    def is_enrolled_on_ironic(self, server_hardware):
        nodes = self.get_oneview_nodes()
        return any(
            node.driver_info.get('server_hardware_uri') == server_hardware.get(
                'uri') for node in nodes)

    def set_attributes_to_object(self, oneview_object_list):
        for oneview_object in oneview_object_list:
            enclosure_group_uri = oneview_object.get('enclosureGroupUri')
            server_group_uri = oneview_object.get("serverGroupUri")
            enclosure_group = self.facade.get_enclosure_group(
                enclosure_group_uri or server_group_uri)

            server_hardware_type = self.facade.get_server_hardware_type(
                oneview_object.get('serverHardwareTypeUri'))
            processor_core_count = oneview_object.get("processorCoreCount", 0)
            processor_count = oneview_object.get("processorCount", 0)

            # Here comes the infamous HACK of local_gb and cpu_arch
            oneview_object["local_gb"] = 120
            oneview_object["cpu_arch"] = 'x86_64'

            oneview_object["uuid"] = common.get_uuid_from_uri(
                oneview_object.get("uri"))

            oneview_object["cpus"] = processor_core_count * processor_count
            oneview_object["memory_mb"] = common.get_attribute_from_dict(
                oneview_object, "memoryMb")

            oneview_object["enclosure_group_name"] = (
                common.get_attribute_from_dict(enclosure_group, 'name'))
            oneview_object["server_hardware_type_name"] = (
                common.get_attribute_from_dict(server_hardware_type, 'name'))

            oneview_object['enrolled'] = self.is_enrolled_on_ironic(
                oneview_object)

    def get_server_hardware_list(self, server_profile_template):
        selected_sht_uri = server_profile_template.get(
            'serverHardwareTypeUri'
        )
        selected_eg_uri = server_profile_template.get(
            'enclosureGroupUri'
        )
        hardware_type_uri = "serverHardwareTypeUri='%s'" % selected_sht_uri

        if selected_eg_uri:
            enclosure_group_uri = "serverGroupUri='%s'" % selected_eg_uri
            server_hardware_list = (
                self.facade.filter_server_hardware_available(
                    [enclosure_group_uri, hardware_type_uri]))
        elif selected_sht_uri:
            # NOTE(fellypefca): Rack Servers are not in any enclosure
            server_hardware_list = (
                self.facade.filter_server_hardware_available(
                    [hardware_type_uri]))
        else:
            server_hardware_list = (
                self.facade.filter_server_hardware_available())
        return sorted(
            server_hardware_list, key=lambda x: x.get('name').lower())

    def create_node(self, args, server_hardware, server_profile_template):
        attrs = self._create_attrs_for_node(
            args, server_hardware, server_profile_template)
        common.update_attrs_for_node(attrs, args, server_hardware)
        node = self.facade.create_ironic_node(**attrs)

        port_creator = port_cmd.PortCreator(self.facade)
        port = port_creator.create_port(args, node)

        if port:
            print("Port %s was created" % port.uuid)

        return node

    @staticmethod
    def _create_attrs_for_node(
            args, server_hardware, server_profile_template):
        if args.name and not common.is_valid_logical_name(args.name):
            msg = "The name '%s' is not a valid logical name." % args.name
            raise Exception(msg)

        if args.name:
            name = args.name
        else:
            name = common.normalize_logical_name(server_hardware.get('name'))

        attrs = common.create_attrs_for_node(
            args, server_hardware, (server_profile_template))
        attrs['name'] = name

        return attrs


@common.arg(
    '-n', '--number',
    metavar='<number>',
    type=int,
    help='Create n nodes based on a given HPE OneView '
         'Server Profile Template.')
@common.arg(
    '--name',
    metavar='<name>',
    help='Name of the Ironic node being created.')
@common.arg(
    '-t', '--server-profile-template',
    metavar='<spt>',
    default=None,
    help='Name, UUID or URI of the HPE OneView Server Profile Template.')
@common.arg(
    '-s', '--server-hardware-uuid',
    metavar='<server_hardware>',
    default=None,
    help='URI or UUID of the HPE OneView Server Hardware.')
@common.arg(
    '--use-oneview-ml2-driver',
    action='store_true',
    default=False,
    help='Whether using the OneView Mechanism Driver.')
@common.arg(
    '--classic',
    action='store_true',
    default=False,
    help='Whether using classic drivers.')
@common.arg(
    '-m', '--mac',
    help='MAC Address of the HPE OneView Server Hardware.')
def do_node_create(args):
    """Create nodes based on available HPE OneView Objects."""
    facade_obj = facade.Facade(args)
    node_creator = NodeCreator(facade_obj)

    try:
        server_hardware = (
            facade_obj.get_server_hardware(args.server_hardware_uuid)
        )
    except Exception:
        print(("Could not find a Server Hardware matching '%s'")
              % args.server_hardware_uuid)
        return

    server_hardware_list = [server_hardware] if server_hardware else None

    try:
        spt_list = facade_obj.list_templates_compatible(server_hardware_list)
    except Exception:
        print(("Unable to retrieve Server Profile Template '%s'")
              % args.server_profile_template)
        return

    node_creator.set_attributes_to_object(spt_list)
    common.assign_elements_with_new_id(spt_list)

    if not args.server_profile_template:
        template_selected = _interactive_template(spt_list)
    else:
        templates = facade_obj.list_all_templates()
        node_creator.set_attributes_to_object(templates)

        if not common.is_valid_spt(templates, (args.server_profile_template)):
            print(("Server Profile template is not valid '%s'")
                  % args.server_profile_template)
            return

        template_selected = common.get_element(
            spt_list, args.server_profile_template
        )

        if not template_selected:
            print(("Server Hardware '%s' does not match the Server Hardware "
                   "Type specified in this Server Profile Template '%s'")
                  % (args.server_hardware_uuid, args.server_profile_template))
            return

    s_hardware_list = node_creator.get_server_hardware_list(template_selected)
    node_creator.set_attributes_to_object(s_hardware_list)
    common.assign_elements_with_new_id(s_hardware_list)

    passed_server_hardware = None
    if args.server_hardware_uuid:
        passed_server_hardware = common.get_element(
            s_hardware_list, args.server_hardware_uuid
        )
        if passed_server_hardware is None:
            print(("Server Hardware (%(sh)s) does not match the Server "
                   "Hardware Type specified in this Server Profile Template "
                   "(%(spt)s)") % {'sh': args.server_hardware_uuid,
                                   'spt': args.server_profile_template})
            return

    if args.mac and not common.is_valid_mac_address(args.mac):
        print(("Node could not be created. '%s' is not a valid MAC address.")
              % args.mac)
        return

    if args.number and not passed_server_hardware:
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
                'Local GB',
                'CPU Arch',
                'Enclosure Group Name',
                'Server Hardware Type Name'
            ]
        )

        nodes_created = 0
        for node_index in range(args.number):
            node = common.get_element_by_id(s_hardware_list, node_index + 1)

            if not node:
                print("{} nodes created.".format(nodes_created))
                break
            elif node_creator.is_enrolled_on_ironic(node):
                print(('Server Hardware %(server_hardware)s is already '
                       'enrolled on Ironic.') % {'server_hardware':
                                                 node.get("uuid")})
            else:
                if node_creator.is_server_profile_applied(node):
                    print(('Server Hardware %(server_hardware)s is in use by '
                           'OneView.') % {'server_hardware':
                                          node.get("uuid")})

                node_creator.create_node(args, node, template_selected)
                nodes_created += 1

        print('Node Creation Finished.')

    else:
        if not passed_server_hardware:
            selected_server_hardware_list = _interactive_server_hardware(
                s_hardware_list)
        else:
            selected_server_hardware_list = [passed_server_hardware]

        not_enrolled_server_hardware = _remove_ironic_enrolled(
            node_creator, selected_server_hardware_list)

        _create_nodes(node_creator, not_enrolled_server_hardware, args,
                      template_selected)


def do_server_profile_template_list(args):
    """List Server Profile Templates of HPE OneView."""
    facade_obj = facade.Facade(args)
    node_creator = NodeCreator(facade_obj)

    spt_list = facade_obj.list_templates_compatible()
    node_creator.set_attributes_to_object(spt_list)

    common.print_prompt(
        spt_list,
        [
            'uuid',
            'name',
            'enclosure_group_name',
            'server_hardware_type_name'
        ],
        field_labels=[
            'UUID',
            'Name',
            'Enclosure Group Name',
            'Server Hardware Type Name'
        ],
        sortby_index=1
    )


@common.arg(
    '-t', '--server-profile-template',
    metavar='<spt>',
    help='Name or UUID of the HPE OneView Server Profile Template.')
def do_server_hardware_list(args):
    """List Server Hardware of HPE OneView."""
    facade_obj = facade.Facade(args)
    node_creator = NodeCreator(facade_obj)

    spt_list = facade_obj.list_templates_compatible()
    node_creator.set_attributes_to_object(spt_list)

    template_selected = {}
    if args.server_profile_template:
        template_selected = common.get_element(
            spt_list, args.server_profile_template
        )

        if template_selected is None:
            print(("Could not find a Server Profile Template matching '%s'")
                  % args.server_profile_template)
            return

    s_hardware_list = node_creator.get_server_hardware_list(
        template_selected
    )
    node_creator.set_attributes_to_object(s_hardware_list)

    common.print_prompt(
        s_hardware_list,
        [
            'uuid',
            'name',
            'cpus',
            'memory_mb',
            'local_gb',
            'enclosure_group_name',
            'server_hardware_type_name'
        ],
        field_labels=[
            'UUID',
            'Name',
            'CPUs',
            'Memory MB',
            'Local GB',
            'Enclosure Group Name',
            'Server Hardware Type Name'
        ],
        sortby_index=1
    )


def _interactive_template(spt_list):
    template_selected = None
    while not template_selected:
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

    print("You choose the following Server Profile Template: ")
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
    return template_selected


def _remove_ironic_enrolled(node_creator, selected_server_hardware_list):
    not_enrolled = []
    for server_hardware in selected_server_hardware_list:
        if node_creator.is_enrolled_on_ironic(server_hardware):
            print(('It was not possible to create the node, the '
                   'Server Hardware %s is enrolled on Ironic.') %
                  server_hardware.get('name'))
        else:
            not_enrolled.append(server_hardware)
    return not_enrolled


def _create_nodes(node_creator, not_enrolled_server_hardware, args,
                  template_selected):
    if not_enrolled_server_hardware:
        print('Creating nodes to represent the following Server Hardware.')
        common.print_prompt(
            not_enrolled_server_hardware,
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
                'Enclosure Group Name',
                'Server Hardware Type Name'
            ]
        )
        for server_hardware in not_enrolled_server_hardware:
            if node_creator.is_server_profile_applied(
                    server_hardware):
                print('The Server Hardware %s is in use by OneView.' %
                      server_hardware.get('name'))

            node = node_creator.create_node(
                args, server_hardware, template_selected
            )

            print('Node ' + node.uuid + ' was created!')


def _interactive_server_hardware(s_hardware_list):
    print('Listing compatible Server Hardware objects...')

    s_hardware_ids_selected = []
    invalid_server_hardware = True
    while invalid_server_hardware:
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
                'Local GB',
                'CPU Arch',
                'Enclosure Group Name',
                'Server Hardware Type Name',
                'Enrolled'
            ]
        )
        if input_id == 'q':
            sys.exit()

        s_hardware_ids_selected = input_id.split()
        invalid_server_hardware = common.is_entry_invalid(
            s_hardware_ids_selected, s_hardware_list)

        s_hardware_ids_selected = input_id.split()

    server_hardware_selected_list = []
    for server_hardware_id in s_hardware_ids_selected:
        server_hardware = common.get_element_by_id(
            s_hardware_list, server_hardware_id
        )
        server_hardware_selected_list.append(server_hardware)

    return server_hardware_selected_list
