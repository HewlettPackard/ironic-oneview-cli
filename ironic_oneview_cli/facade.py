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

from ironic_oneview_cli.common import get_oneview_client
from ironic_oneview_cli.openstack_client import get_ironic_client
from ironic_oneview_cli.openstack_client import get_nova_client


class Facade(object):

    def __init__(self, args):
        self.ironicclient = get_ironic_client(args)
        self.novaclient = get_nova_client(args)
        self.oneview_client = get_oneview_client(
            manager_url=args.ov_auth_url,
            username=args.ov_username,
            password=args.ov_password,
            allow_insecure_connections=args.insecure,
            tls_cacert_file=args.ov_cacert
        )

    # =========================================================================
    # Ironic actions
    # =========================================================================
    def get_ironic_node_list(self):
        return self.ironicclient.node.list(detail=True)

    def get_ironic_node(self, node_uuid):
        return self.ironicclient.node.get(node_uuid)

    def node_set_maintenance(self, node_uuid, maintenance_mode, maint_reason):
        return self.ironicclient.node.set_maintenance(
            node_uuid, maintenance_mode, maint_reason=maint_reason)

    def create_ironic_node(self, **attrs):
        return self.ironicclient.node.create(**attrs)

    def get_drivers(self):
        return self.ironicclient.driver.list()

    # =========================================================================
    # Nova actions
    # =========================================================================
    def create_nova_flavor(self, **attrs):
        return self.novaclient.flavors.create(
            name=attrs.get('name'),
            ram=attrs.get('ram'),
            vcpus=attrs.get('vcpus'),
            disk=attrs.get('disk')
        )

    # =========================================================================
    # OneView actions
    # =========================================================================
    def get_server_hardware(self, uri):
        uuid = uri[uri.rfind("/") + 1:]
        return self.oneview_client.server_hardware.get(uuid)

    def get_server_profile_template(self, uri):
        uuid = uri[uri.rfind("/") + 1:]
        return self.oneview_client.server_profile_template.get(uuid)

    def get_enclosure_group(self, uri):
        uuid = uri[uri.rfind("/") + 1:]
        return self.oneview_client.enclosure_group.get(uuid)

    def get_server_hardware_type(self, uri):
        uuid = uri[uri.rfind("/") + 1:]
        return self.oneview_client.server_hardware_type.get(uuid)

    # Next generation
    def list_server_hardware_available(self):
        server_hardware_list = self.filter_server_hardware_available()
        return [sh for sh in server_hardware_list if not sh.server_profile_uri]

    def list_templates_compatible_with(self, server_hardware_list):
        compatible_server_profile_list = []
        server_hardware_type_list = []
        server_group_list = []

        for server_hardware in server_hardware_list:
            server_hardware_type_list.append(
                server_hardware.server_hardware_type_uri)
            server_group_list.append(
                server_hardware.enclosure_group_uri)

        spt_list = self.oneview_client.server_profile_template.list()
        for spt in spt_list:
            if (spt.server_hardware_type_uri in server_hardware_type_list and
               spt.enclosure_group_uri in server_group_list):
                compatible_server_profile_list.append(spt)
        return compatible_server_profile_list

    def filter_server_hardware_available(self, **kwargs):
        return self.oneview_client.server_hardware.list(**kwargs)
