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

# from oslo_config import cfg

from ironic_oneview_cli.oneview_client import OneViewClient
from ironic_oneview_cli.openstack_client import OpenstackClient
from ironic_oneview_cli.openstack_client import get_ironic_client


class Facade(object):

    def __init__(self, config):
        self.ironicclient = get_ironic_client(config)
#         self.oneviewclient =

    #===============================================================================
    # Ironic actions
    #===============================================================================
    def update_ironic_node_state(self, node, server_hardware_uri):
        return os_client._update_ironic_node_state(node, server_hardware_uri)

    def get_ironic_node_list(self):
        return self.ironicclient.node.list(detail=True)

    def get_ironic_node(self, node_uuid):
        return self.ironicclient.node.get(node_uuid)

    def node_set_maintenance(self, node_uuid, maintenance_mode, maint_reason):
        return self.ironicclient.node.set_maintenance(node_uuid, maintenance_mode, maint_reason=maint_reason)

    def create_ironic_node(self, **attrs):
        return self.ironicclient.node.create(**attrs)

    #===============================================================================
    # Nova actions
    #===============================================================================

    def get_nova_client(self):
        return os_client.get_nova_client()


    def is_nova_flavor_available(self, server_hardware_info):
        return os_client._is_flavor_available(server_hardware_info)


    #===============================================================================
    # OneView actions
    #===============================================================================

    def prepare_and_do_ov_requests(self, uri, body={}, request_type='GET', api_version='120'):
        return ov_client.prepare_and_do_request(uri, body, request_type, api_version)


    def get_server_hardware(self, uri):
        return sh_api.get(uri)


    def parse_server_hardware_to_dict(self, server_hardware_json):
        return ov_client.server_hardware_api.parse_server_hardware_to_dict(server_hardware_json)


    def get_ov_server_hardware_list(self,):
        return ov_client.server_hardware_api.get_server_hardware_list()


    def get_ov_server_power_state(self, driver_info):
        return ov_client.server_hardware_api.get_node_power_state(driver_info)

