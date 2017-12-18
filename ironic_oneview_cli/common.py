# Copyright (2015-2017) Hewlett Packard Enterprise Development LP
# Copyright (2015-2017) Universidade Federal de Campina Grande
# Copyright 2012 Red Hat, Inc.
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

from builtins import input as builtin_input
import prettytable
import six
from six.moves import urllib

from oslo_utils import encodeutils
from oslo_utils import importutils

hpclient = importutils.try_import('hpOneView.oneview_client')

# NOTE(fellypefca): Classic Drivers will be deprecated on Openstack Queens
SUPPORTED_DRIVERS = ['agent_pxe_oneview', 'iscsi_pxe_oneview', 'fake_oneview']
SUPPORTED_HARDWARE_TYPES = ['oneview']


def get_hponeview_client(args):
    """Generate an instance of the hpOneView client.

    Generates an instance of the hpOneView client using the hpOneView library.

    :returns: an instance of the OneView client
    """
    return hpclient.OneViewClient({"ip": args.ov_auth_url,
                                   "credentials": {
                                       "userName": args.ov_username,
                                       "password": args.ov_password}})


def get_uuid_from_uri(uri):
    if uri:
        return uri.split("/")[-1]


def arg(*args, **kwargs):
    """Decorator for CLI args.

    Example:

    >>> @arg("name", help="Name of the new entity")
    ... def entity_create(args):
    ...     pass
    """
    def _decorator(func):
        add_arg(func, *args, **kwargs)
        return func
    return _decorator


def add_arg(func, *args, **kwargs):
    """Bind CLI arguments to a shell.py `do_foo` function."""
    if not hasattr(func, 'arguments'):
        func.arguments = []

    # NOTE(sirp): avoid dups that can occur when the module is shared across
    # tests.
    if (args, kwargs) not in func.arguments:
        # Because of the semantics of decorator composition if we just append
        # to the options list positional options will appear to be backwards.
        func.arguments.insert(0, (args, kwargs))


def env(*args, **kwargs):
    """Return the first environment variable set.

    If all are empty, defaults to '' or keyword arg `default`.
    """
    for argument in args:
        value = os.environ.get(argument)
        if value:
            return value
    return kwargs.get('default', '')


def _print_list(objs, fields, sortby_index=0, field_labels=None):
    """Print a list or objects as a table, one row per object.

    :param objs: iterable of :class:`Resource`
    :param fields: attributes that correspond to columns, in order
    :param sortby_index: index of the field for sorting table rows
    :param field_labels: Labels to use in the heading of the table, default to
        fields.
    """
    formatters = {}
    mixed_case_fields = []
    field_labels = field_labels or fields
    if len(field_labels) != len(fields):
        raise ValueError(("Field labels list %(labels)s has different number "
                          "of elements than fields list %(fields)s"),
                         {'labels': field_labels, 'fields': fields})

    if sortby_index is None:
        kwargs = {}
    else:
        kwargs = {'sortby': field_labels[sortby_index]}
    pt = prettytable.PrettyTable(field_labels)
    pt.align = 'l'

    for o in objs:
        row = []
        for field in fields:
            if field in formatters:
                row.append(formatters[field](o))
            else:
                if field in mixed_case_fields:
                    field_name = field.replace(' ', '_')
                else:
                    field_name = field.lower().replace(' ', '_')
                data = o.get(field_name)
                row.append(data)
        pt.add_row(row)

    if six.PY3:
        print(encodeutils.safe_encode(pt.get_string(**kwargs)).decode())
    else:
        print(encodeutils.safe_encode(pt.get_string(**kwargs)))


def print_prompt(object_list, header_list, input_message=None,
                 field_labels=None):
    _print_list(
        object_list,
        header_list,
        field_labels=field_labels
    )
    if input_message is not None:
        input_value = builtin_input(input_message)
        return input_value


def assign_elements_with_new_id(element_list):
    counter = 1
    for element in element_list:
        element['id'] = counter
        counter += 1


def get_element_by_id(element_list, element_id):
    try:
        for element in element_list:
            if element['id'] == int(element_id):
                return element
    except Exception:
        return


def get_element_by_name(element_list, element_name):
    try:
        for element in element_list:
            if element['name'] == element_name:
                return element
    except Exception:
        return


def is_entry_invalid(entries, objects_list):
    if not entries:
        return True
    for entry in entries:
        element = get_element_by_id(objects_list, entry)
        if element is None:
            return True
    return False


def set_flavor_name(flavor):
    flavor_name_template = "%sMB-RAM_%s_%s_%s" % (flavor.get('ram_mb'),
                                                  flavor.get('cpus'),
                                                  flavor.get('cpu_arch'),
                                                  flavor.get('disk'))
    flavor_name = builtin_input(
        "Insert a name for the Flavor. [%(default_name)s]> " %
        {'default_name': flavor_name_template}
    )

    if not flavor_name:
        return flavor_name_template
    return flavor_name


def get_attribute_from_dict(dictionary, keyword, default_value=''):
    """Get value from a dictionary if the dictionary exists.

    :param dictionary: 'dict' with the elements
    :param keyword: attributes that correspond to a key in the dict
    :param default_value: The default value returned if the dictionary does not
        exist or if the keyword does not exist.
    :returns: The value to keyword or the default value.
    """
    if dictionary:
        return dictionary.get(keyword, default_value)
    return default_value


def approve_command_prompt(message):
    response = builtin_input(message)
    return response.lower() == 'y'


def get_oneview_nodes(ironic_nodes):
    """Get the nodes which drivers are compatible with OneView.

    :param ironic_nodes: A list of Ironic Nodes
    :returns: A list of Ironic Nodes with OneView compatible Drivers and
              Hardware types only.
    """
    oneview_nodes = [node for node in ironic_nodes if node.driver in
                     SUPPORTED_DRIVERS + SUPPORTED_HARDWARE_TYPES]
    return oneview_nodes


def is_server_profile_applied(server_hardware):
    return bool(server_hardware.get('serverProfileUri'))


def create_attrs_for_node(
        args, server_hardware, server_profile_template):
    attrs = {
        'driver_info': {
            'deploy_kernel': args.os_ironic_deploy_kernel_uuid,
            'deploy_ramdisk': args.os_ironic_deploy_ramdisk_uuid,
            'server_hardware_uri': server_hardware.get('uri'),
            'use_oneview_ml2_driver': args.use_oneview_ml2_driver,
        },
        'properties': {
            'capabilities': 'server_hardware_type_uri:%s,'
                            'server_profile_template_uri:%s' % (
                                server_hardware.get(
                                    'serverHardwareTypeUri'),
                                server_profile_template.get('uri')
                            )
        }
    }

    if args.classic:
        attrs['driver'] = args.os_ironic_node_driver
    else:
        attrs['driver'] = args.os_driver
        attrs['power_interface'] = args.os_power_interface
        attrs['management_interface'] = args.os_management_interface
        attrs['inspect_interface'] = args.os_inspect_interface
        attrs['deploy_interface'] = args.os_deploy_interface

    return attrs


def update_attrs_for_node(attributes, args, server_hardware):
    if args.use_oneview_ml2_driver:
        attributes['network_interface'] = 'neutron'

    if server_hardware.get('serverGroupUri'):
        enclosure_group_uri = (
            ',enclosure_group_uri:%s' % server_hardware.get(
                'serverGroupUri')
        )
        attributes['properties']['capabilities'] += enclosure_group_uri

    if not args.os_inspection_enabled:
        cpus = (server_hardware.get('processorCoreCount') *
                server_hardware.get('processorCount'))
        hardware_properties = {
            'cpus': cpus,
            'memory_mb': server_hardware.get('memoryMb'),
            'local_gb': server_hardware.get('local_gb'),
            'cpu_arch': server_hardware.get('cpu_arch')
        }

        attributes['properties'].update(hardware_properties)


def get_first_ethernet_physical_port(server_hardware):
    for device in server_hardware.get('portMap').get(
            'deviceSlots'):
        for physical_port in device.get('physicalPorts', []):
            if physical_port.get('type') == 'Ethernet':
                return physical_port


def create_attrs_for_port(ironic_node, mac):
    attrs = {
        'address': mac,
        'node_uuid': ironic_node.uuid,
        'portgroup_uuid': None,
        "local_link_connection": build_local_link_connection(ironic_node),
        'pxe_enabled': True
    }

    return attrs


def set_flavor_properties(
        node, server_hardware_type, enclosure_group, server_profile_template):
    flavor = {}

    flavor['ram_mb'] = node.properties.get('memory_mb')
    flavor['cpus'] = node.properties.get('cpus')
    flavor['disk'] = node.properties.get('local_gb')
    flavor['cpu_arch'] = node.properties.get('cpu_arch')
    flavor['server_hardware_type_name'] = (
        get_attribute_from_dict(server_hardware_type, 'name'))
    flavor['server_hardware_type_uri'] = (
        get_attribute_from_dict(server_hardware_type, 'uri'))
    flavor['enclosure_group_name'] = (
        get_attribute_from_dict(enclosure_group, 'name'))
    flavor['enclosure_group_uri'] = (
        get_attribute_from_dict(enclosure_group, 'uri'))
    flavor['server_profile_template_name'] = (
        get_attribute_from_dict(server_profile_template, 'name'))
    flavor['server_profile_template_uri'] = (
        get_attribute_from_dict(server_profile_template, 'uri'))

    return flavor


def build_local_link_connection(ironic_node):
    local_link_connection = {}
    if ironic_node.driver_info.get('use_oneview_ml2_driver'):
        server_hardware_id = get_server_hardware_id_from_node(ironic_node)
        switch_info = (
            '{"server_hardware_id": "%(server_hardware_id)s", '
            '"bootable": "%(bootable)s"}') % {
                'server_hardware_id': server_hardware_id,
                'bootable': True}
        local_link_connection = {
            "switch_id": "01:23:45:67:89:ab",
            "port_id": "",
            "switch_info": switch_info
        }
    return local_link_connection


def get_server_hardware_id_from_node(ironic_node):
    """Get the Server Hardware id from a ironic_node.

    :param ironic_node: A Ironic Node
    :return: The Server hardware id
    """
    server_hardware_uri = ironic_node.driver_info.get(
        'server_hardware_uri')
    return get_uuid_from_uri(server_hardware_uri)


def get_ilo_access(remote_console):
    """Get the needed information to access ilo.

    Get the host_ip and a token of an iLO remote console instance which can be
    used to perform operations on that controller.

    The Remote Console url has the following format:
    hplocons://addr=1.2.3.4&sessionkey=a79659e3b3b7c8209c901ac3509a6719

    :param: remote_console: OneView Remote Console object with a
            remoteConsoleUrl
    :returns: A tuple with the Host IP and Token to access ilo, for
              example: ('1.2.3.4', 'a79659e3b3b7c8209c901ac3509a6719')
    """
    url = remote_console.get('remoteConsoleUrl')
    url_parse = urllib.parse.urlparse(url)
    host_ip = urllib.parse.parse_qs(url_parse.netloc).get('addr')[0]
    token = urllib.parse.parse_qs(url_parse.netloc).get('sessionkey')[0]
    return host_ip, token
