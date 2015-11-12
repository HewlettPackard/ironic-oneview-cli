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

import abc
import six

from ironic_oneview_cli.oneview_client import OneViewClient


class Resource(object):
    six.add_metaclass(abc.ABCMeta)

    def __init__(self, _id, info):
        self.id = _id
        self._info = info
        self._add_details(info)

    def _add_details(self, info):
        for (k, v) in six.iteritems(info):
            try:
                setattr(self, k, v)
                self._info[k] = v
            except AttributeError:
                pass


class ServerProfile(Resource):
    def __repr__(self):
        return "<ServerProfile uri='%s'>" % self.uri


class ServerHardware(Resource):
    def __repr__(self):
        return "<ServerHardware uri='%s'>" % self.uri


class Manager(object):
    six.add_metaclass(abc.ABCMeta)
    resource_class = None

    def __init__(self, config):
        allow_insecure_connections = False
        if config.oneview.allow_insecure_connections.lower() == 'true':
            allow_insecure_connections = True
        self.oneviewclient = OneViewClient(
            config.oneview.manager_url,
            config.oneview.username,
            config.oneview.password,
            allow_insecure_connections,
            config.oneview.tls_cacert_file
        )

    def _dict_to_object(self, dictionary):
        raise Exception('Not Implemented')

    def get(self, uri):
        return self._dict_to_object(self.api.get(uri))

    def list(self, **kwargs):
        objects = []
        items = self.api.list(**kwargs)

        for i in range(len(items)):
            objects.append(self._dict_to_object(items[i], i))

        return objects


class ServerProfileManager(Manager):
    resource_class = ServerProfile
    fields = ['serverHardwareTypeUri', 'description', 'name',
              'enclosureGroupUri', 'uri', ]

    def __init__(self, config_file):
        super(ServerProfileManager, self).__init__(config_file)
        self.api = self.oneviewclient.server_profile

    def _dict_to_object(self, dict, id=0):

        filtered_server_profile_dict = {}
        for field in self.fields:
            filtered_server_profile_dict[field] = dict[field]

        filtered_server_profile_dict['serverHardwareTypeName'] = \
            self.oneviewclient.server_hardware_type.get(
                filtered_server_profile_dict['serverHardwareTypeUri'], 'name')
        filtered_server_profile_dict['enclosureGroupName'] = \
            self.oneviewclient.enclosure_group.get(
                filtered_server_profile_dict['enclosureGroupUri'], 'name')

        return ServerProfile(id, filtered_server_profile_dict)

    def server_profile_template_list(self):
        objects = []
        templates = self.api.template_list()

        for i in range(len(templates)):
            objects.append(self._dict_to_object(templates[i], i))

        return objects

    def list_templates_compatible_with(self, server_hardware_list):
        compatible_server_profile_list = []
        server_hardware_type_list = []
        server_group_list = []

        for server_hardware in server_hardware_list:
            server_hardware_type_list.append(
                server_hardware.serverHardwareTypeUri)
            server_group_list.append(
                server_hardware.serverGroupUri)

        server_profile_list = self.server_profile_template_list()
        for server_profile in server_profile_list:
            if server_profile.serverHardwareTypeUri in\
                server_hardware_type_list and\
                server_profile.enclosureGroupUri in server_group_list:
                    compatible_server_profile_list.append(server_profile)

        return compatible_server_profile_list


class ServerHardwareManager(Manager):
    resource_class = ServerHardware
    fields = ['uri', 'serverHardwareTypeUri', 'uuid', 'memoryMb',
              'description', 'serverGroupUri', 'name', 'serverProfileUri']

    def __init__(self, config_file):
        super(ServerHardwareManager, self).__init__(config_file)
        self.api = self.oneviewclient.server_hardware

    def _dict_to_object(self, dict, id=0):

        filtered_server_profile_dict = {}
        for field in self.fields:
            filtered_server_profile_dict[field] = dict[field]

        filtered_server_profile_dict['cpus'] = dict['processorCoreCount'] * \
            dict['processorCount']
        filtered_server_profile_dict['cpu_arch'] = 'x86_64'
        filtered_server_profile_dict['local_gb'] = 120

        filtered_server_profile_dict['serverHardwareTypeName'] = \
            self.oneviewclient.server_hardware_type.get(
                filtered_server_profile_dict['serverHardwareTypeUri'], 'name')
        filtered_server_profile_dict['serverGroupName'] = \
            self.oneviewclient.enclosure_group.get(
                filtered_server_profile_dict['serverGroupUri'], 'name')

        return ServerHardware(id, filtered_server_profile_dict)
