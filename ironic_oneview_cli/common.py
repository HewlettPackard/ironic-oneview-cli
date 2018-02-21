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
import re
import six
from six.moves.urllib import parse

from oslo_utils import encodeutils
from oslo_utils import importutils
import prettytable

from ironicclient import client as ironic_client
from keystoneauth1 import loading
from keystoneauth1 import session
from novaclient import client as nova_client

from ironic_oneview_cli import exceptions

oneview_client = importutils.try_import('hpOneView.oneview_client')
oneview_exceptions = importutils.try_import('hpOneView.exceptions')

# NOTE(fellypefca): Classic Drivers will be deprecated on Openstack Queens
SUPPORTED_DRIVERS = ['agent_pxe_oneview', 'iscsi_pxe_oneview', 'fake_oneview']
SUPPORTED_HARDWARE_TYPES = ['oneview']

_is_valid_logical_name_re = re.compile(r'^[A-Z0-9-._~]+$', re.I)

IRONIC_API_VERSION = 1
NOVA_API_VERSION = 2


def get_ironic_client(args):
    cli_kwargs = {
        'ironic_url': args.ironic_url,
        'os_username': args.os_username,
        'os_password': args.os_password,
        'os_auth_url': args.os_auth_url,
        'os_project_id': args.os_project_id,
        'os_project_name': args.os_project_name,
        'os_tenant_name': args.os_tenant_name,
        'os_region_name': args.os_region_name,
        'os_service_type': args.os_service_type,
        'os_endpoint_type': args.os_endpoint_type,
        'insecure': args.insecure,
        'os_cacert': args.os_cacert,
        'os_cert': args.os_cert,
        'os_ironic_api_version': args.ironic_api_version,
        'os_project_domain_id': args.os_project_domain_id,
        'os_project_domain_name': args.os_project_domain_name,
        'os_user_domain_id': args.os_user_domain_id,
        'os_user_domain_name': args.os_user_domain_name
    }

    return ironic_client.get_client(IRONIC_API_VERSION, **cli_kwargs)


def get_nova_client(args):
    loader = loading.get_plugin_loader('password')
    auth = loader.load_from_options(
        auth_url=args.os_auth_url,
        username=args.os_username,
        password=args.os_password,
        user_domain_id=args.os_user_domain_id,
        user_domain_name=args.os_user_domain_name,
        project_id=args.os_project_id or args.os_tenant_id,
        project_name=args.os_project_name or args.os_tenant_name,
        project_domain_id=args.os_project_domain_id,
        project_domain_name=args.os_project_domain_name
    )

    verify = True
    if args.insecure:
        verify = False
    elif args.os_cacert:
        verify = args.os_cacert

    sess = session.Session(auth=auth, verify=verify, cert=args.os_cert)
    nova = nova_client.Client(NOVA_API_VERSION, session=sess)

    return nova


def get_hponeview_client(args):
    """Generate an instance of the HPE OneView client.

    :returns: an instance of the HPE OneView client.
    :raises: OneViewConnectionError if try a secure connection without a CA
             certificate file path in Ironic OneView CLI configuration file.
    """
    ssl_certificate = args.ov_cacert
    insecure = True if args.ov_insecure.lower() == "true" else False

    if not (insecure or ssl_certificate):
        raise exceptions.OneViewConnectionError(
            "Failed to start Ironic OneView CLI. Attempting to open secure "
            "connection to OneView but CA certificate file is missing. Please "
            "check your configuration file.")

    if insecure:
        print("Ironic OneView CLI is opening an insecure connection to "
              "HPE OneView. We recommend you to configure secure connections "
              "with a CA certificate file.")

        if ssl_certificate:
            print("Insecure connection to OneView, the CA certificate: %s "
                  "will be ignored." % ssl_certificate)
            ssl_certificate = None

    config = {
        "ip": args.ov_auth_url,
        "credentials": {
            "userName": args.ov_username,
            "password": args.ov_password
        },
        "ssl_certificate": ssl_certificate
    }

    try:
        client = oneview_client.OneViewClient(config)
    except oneview_exceptions.HPOneViewException as ex:
        print("Ironic OneView CLI could not open a connection to HPE OneView. "
              "Check credentials and/or CA certificate file. See details on "
              "error below:\n")
        raise ex

    return client


def get_uuid_from_uri(uri):
    if uri:
        return uri.split("/")[-1]
    msg = "OneView Resource URI not found."
    raise exceptions.OneViewResourceNotFoundError(msg)


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
                          "of elements than fields list %(fields)s") %
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
                 field_labels=None, sortby_index=0):
    _print_list(
        object_list,
        header_list,
        field_labels=field_labels,
        sortby_index=sortby_index
    )
    if input_message:
        input_value = builtin_input(input_message)
        return input_value
    return None


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
        return None
    except Exception:
        print("Failed to get element by id.")


def get_element(element_list, element_uuid_name_uri):
    def is_equal(obj, field, value):
        if isinstance(obj, dict):
            return obj.get(field, "") == value
        return getattr(obj, field, "") == value

    for element in element_list:
        if (is_equal(element, 'uuid', element_uuid_name_uri) or
                is_equal(element, 'name', element_uuid_name_uri) or
                is_equal(element, 'uri', element_uuid_name_uri)):
            return element

    return None


def get_element_by_name(element_list, element_name):
    try:
        for element in element_list:
            if element['name'] == element_name:
                return element
        return None
    except Exception:
        print("Failed to get element by name.")


def is_entry_invalid(entries, objects_list):
    if not entries:
        return True
    for entry in entries:
        element = get_element_by_id(objects_list, entry)
        if element is None:
            return True
    return False


def is_valid_logical_name(hostname):
    """Determine if a logical name is valid.

    The logical name may only consist of RFC3986 unreserved
    characters, to wit:
    ALPHA / DIGIT / "-" / "." / "_" / "~"
    """
    if not isinstance(hostname, six.string_types) or len(hostname) > 255:
        return False

    return _is_valid_logical_name_re.match(hostname) is not None


def is_valid_mac_address(mac):
    """Determine if a mac address is valid"""

    return re.match("[0-9a-f]{2}([-:])[0-9a-f]{2}(\\1[0-9a-f]{2}){4}$",
                    mac.lower())


def normalize_logical_name(hostname):
    """Normalize a hostname to be a valid logical name.

    The logical name may only consist of RFC3986 unreserved
    characters, to wit: ALPHA / DIGIT / "-" / "." / "_" / "~"
    This will transform all letters to lowercase, replace spaces
    by underscore and remove any character that does not comply
    with the hostname constraint
    """
    if isinstance(hostname, six.string_types):
        hostname = hostname.replace(' ', '_')

        normalized_hostname = [char for char in hostname
                               if _is_valid_logical_name_re.match(char)]

        return ''.join(normalized_hostname)
    return None


def generate_template_flavor_name(flavor_dict):
    flavor_name_template = "%sMB-RAM_%s_%s_%s" % (
        flavor_dict.get('ram_mb'), flavor_dict.get('cpus'),
        flavor_dict.get('cpu_arch'), flavor_dict.get('disk')
    )
    return flavor_name_template


def set_flavor_name(flavor):
    flavor_name_template = generate_template_flavor_name(flavor)
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
    types = SUPPORTED_DRIVERS + SUPPORTED_HARDWARE_TYPES
    return [i for i in ironic_nodes if i.driver in types]


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
    try:
        for device in server_hardware.get('portMap').get(
                'deviceSlots'):
            for physical_port in device.get('physicalPorts', []):
                if physical_port.get('type') == 'Ethernet':
                    return physical_port
        print("Could not find any physical port with the type Ethernet on "
              "the Server Hardware: %s" % server_hardware)
        return None
    except oneview_exceptions.HPOneViewException as ex:
        msg = ("Could not get the physical_port of Server Hardware: %s" %
               server_hardware)
        raise ex(msg)


def create_attrs_for_port(ironic_node, mac):
    attrs = {
        'address': mac,
        'node_uuid': ironic_node.uuid,
        'portgroup_uuid': None,
        "local_link_connection": build_local_link_connection(ironic_node),
        'pxe_enabled': True
    }

    return attrs


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
    url_parse = parse.urlparse(url)
    host_ip = parse.parse_qs(url_parse.netloc).get('addr')[0]
    token = parse.parse_qs(url_parse.netloc).get('sessionkey')[0]
    return host_ip, token


def get_server_profile_compatible(server_profile_templates, server_hardware):
    """Get server profiles compatible with server hardware.

    :param server_profile_templates: List of server profile templates
    :param server_hardware: Server Hardware object
    :return: List of server profiles templates compatible with server hardware
             sorted by name
    """
    server_profile_list = []
    server_hardware_type_list = []
    server_group_list = []
    for hardware in server_hardware:
        server_hardware_type_list.append(
            hardware.get('serverHardwareTypeUri'))
        server_group_list.append(
            hardware.get('serverGroupUri'))

    for spt in server_profile_templates:
        if (spt.get('serverHardwareTypeUri') in server_hardware_type_list and
                spt.get('enclosureGroupUri') in server_group_list):
            server_profile_list.append(spt)

    return sorted(server_profile_list, key=lambda x: x.get('name').lower())


def is_valid_spt(server_profile_templates, template_uri):
    valid = get_element(server_profile_templates, template_uri)
    if valid is None:
        return False
    return True
