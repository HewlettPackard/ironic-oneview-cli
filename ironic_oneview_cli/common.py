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
                 field_labels=None):
    _print_list(
        object_list,
        header_list,
        field_labels=field_labels
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
