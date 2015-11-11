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

import json
import requests

from ironic_oneview_cli import oneview_uri
from ironic_oneview_cli import service_logging as logging
from ironic_oneview_cli.sync_exceptions import OneViewConnectionError


LOG = logging.getLogger(__name__)

ONEVIEW_POWER_ON = 'On'
ONEVIEW_POWER_OFF = 'Off'
ONEVIEW_REST_API_VERSION = '200'


def get_oneview_client(conf):
    kwargs = {
        'username': conf.oneview.username,
        'password': conf.oneview.password,
        'manager_url': conf.oneview.manager_url,
        'allow_insecure_connections': False,
        'tls_cacert_file': conf.oneview.tls_cacert_file
    }
    if conf.oneview.allow_insecure_connections.lower() == 'true':
        kwargs['allow_insecure_connections'] = True
        print(
            "InsecureRequestWarning: Unverified HTTPS requests are being made."
            " Adding certificate verification is strongly advised. See: "
            "https://urllib3.readthedocs.org/en/latest/security.html"
        )
    if conf.oneview.tls_cacert_file:
        kwargs['tls_cacert_file'] = conf.oneview.tls_cacert_file
    return OneViewClient(**kwargs)


class OneViewRequestAPI(object):
    def __init__(self, manager_url, username, password,
                 allow_insecure_connections, tls_cacert_file):
        self.token = None
        self.manager_url = manager_url
        self.username = username
        self.password = password
        self.tls_cacert_file = tls_cacert_file
        self.allow_insecure_connections = allow_insecure_connections

    def _get_verify_connection_option(self):
        verify_status = False
        if self.allow_insecure_connections is False:
            if self.tls_cacert_file:
                verify_status = self.tls_cacert_file
            else:
                verify_status = True
        return verify_status

    def _is_token_valid(self):
        return self.token is not None

    def _try_execute_request(self, url, request_type, body, headers,
                             verify_status):
        try:
            requests.packages.urllib3.disable_warnings()
            return requests.request(request_type, url, data=json.dumps(body),
                                    headers=headers, verify=verify_status)
        except requests.RequestException as ex:
            LOG.error(("Can't connect to OneView: %s")
                      % (str(ex.message).split(':')[-1]))
            raise OneViewConnectionError(
                "Can't connect to OneView: %s" % str(ex.message))

    def _new_token(self):
        LOG.info(("Using OneView credentials specified in synch.conf"))
        url = '%s%s' % (self.manager_url,
                        oneview_uri.AUTHENTICATION_URL)
        body = {
            'password': self.password,
            'userName': self.username
        }
        headers = {'content-type': 'application/json'}
        verify_status = self._get_verify_connection_option()
        if verify_status is False:
            LOG.warn('Using insecure connection')
        json_response = None
        repeat = True
        while repeat:
            r = self._try_execute_request(url, 'POST', body, headers,
                                          verify_status)
            # NOTE: Workaround to fix JsonDecode problems
            try:
                json_response = r.json()
                repeat = self._check_request_status(r)
            except Exception:
                repeat = True
        return json_response.get('sessionID')

    def _update_token(self):
        if not self._is_token_valid():
            self.token = self._new_token()

    def _check_request_status(self, response):
        repeat = False
        status = response.status_code
        response_json = response.json()
        if status in (409,):
            ignored_conflicts = {'RABBITMQ_CLIENTCERT_CONFLICT'}
            if (response_json.get('errorCode') in ignored_conflicts):
                repeat = False
            else:
                repeat = True
            LOG.debug("Conflict contacting OneView: ", response_json)
        elif status in (404, 500):
            LOG.error(("Error contacting OneView: "), response_json)
        elif status not in (200, 202):
            message = ("Status %(status_code)s not recognized: %(ret_json)s" %
                       {"status_code": status, "ret_json": response_json})
            LOG.warn(message)

        return repeat

    def prepare_and_do_request(self, uri, body={}, request_type='GET'):
        self._update_token()

        if self.token is None:
            raise OneViewConnectionError(
                "Acess to OneView Not Authorized. Check the OneView credential"
                " in the configuration file.")

        headers = {
            'content-type': 'application/json',
            'X-Api-Version': ONEVIEW_REST_API_VERSION,
            'Auth': self.token
        }
        url = '%s%s' % (self.manager_url, uri)
        verify_status = self._get_verify_connection_option()
        json_response = None
        repeat = True
        while repeat:
            r = self._try_execute_request(url, request_type, body, headers,
                                          verify_status)
            # NOTE: Workaround to fix JsonDecode problems
            try:
                json_response = r.json()
                repeat = self._check_request_status(r)
            except Exception:
                repeat = True
        return json_response


class ResourceAPI(OneViewRequestAPI):
    def get(self, uri, field=None):
        resource = self.prepare_and_do_request(uri)
        return resource if field is None else resource[field]

    def _list(self, uri, fields=None):
        obj_list = self.prepare_and_do_request(uri).get("members")
        if fields is None:
            return obj_list

        filtered_list = []

        for obj_dict in obj_list:
            if self._is_dict_elegible(obj_dict, fields):
                filtered_list.append(obj_dict)

        return filtered_list

    def _is_dict_elegible(self, obj_dict, fields):
        for key, value in fields.items():
            if obj_dict[key] != value:
                return False
        return True


class OneViewCertificateAPI(ResourceAPI):
    def get_certificate(self):
        return self.get(oneview_uri.CERTIFICATE_AND_KEY_URI,
                        'base64SSLCertData')

    def get_key(self):
        return self.get(oneview_uri.CERTIFICATE_AND_KEY_URI,
                        'base64SSLKeyData')

    def get_ca(self):
        return self.get(oneview_uri.CA_URI)

    def post_certificate(self):
        body = {'type': 'RabbitMqClientCertV2', 'commonName': 'default'}

        return self.prepare_and_do_request(oneview_uri.CERTIFICATE_RABBIT_MQ,
                                           body=body, request_type='POST')


class OneViewServerHardwareTypeAPI(ResourceAPI):
    pass


class OneViewEnclosureGroupAPI(ResourceAPI):
    pass


class OneViewServerHardwareAPI(ResourceAPI):
    def list(self, only_available=False, fields=None):
        uri = "/rest/server-hardware?start=0&count=-1"
        if only_available:
            if fields is None:
                fields = {}
            fields['serverProfileUri'] = None
        return self._list(uri, fields)

    def parse_server_hardware_to_dict(self, server_hardware):
        port_map = server_hardware.get('portMap')
        try:
            physical_ports = port_map.get('deviceSlots')[0].get(
                'physicalPorts')
            mac_address = physical_ports[0].get('mac')
        except Exception:
            raise Exception("Server hardware primary physical NIC not found.")
        vcpus = (server_hardware["processorCoreCount"] *
                 server_hardware["processorCount"])
        return {'name': server_hardware["name"],
                'cpus': vcpus,
                'memory_mb': server_hardware["memoryMb"],
                'local_gb': 120,
                'server_hardware_uri': server_hardware["uri"],
                'server_hardware_type_uri':
                    server_hardware["serverHardwareTypeUri"],
                'enclosure_group_uri': server_hardware['serverGroupUri'],
                'cpu_arch': 'x86_64',
                'mac': mac_address,
                'server_profile_uri': server_hardware.get('serverProfileUri')
                }


class OneViewServerProfileAPI(ResourceAPI):

    def list(self):
        return self._list(oneview_uri.SERVER_PROFILE_LIST_URI)

    def template_list(self):
        return [server_profile for server_profile in self.list() if
                server_profile.get('serverHardwareUri') is None]


class OneViewClient(object):
    def __init__(self, manager_url, username, password,
                 allow_insecure_connections, tls_cacert_file):
        self.certificate = OneViewCertificateAPI(
            manager_url,
            username,
            password,
            allow_insecure_connections,
            tls_cacert_file
        )
        self.server_hardware = OneViewServerHardwareAPI(
            manager_url,
            username,
            password,
            allow_insecure_connections,
            tls_cacert_file
        )
        self.server_profile = OneViewServerProfileAPI(
            manager_url,
            username,
            password,
            allow_insecure_connections,
            tls_cacert_file
        )
        self.server_hardware_type = OneViewServerHardwareTypeAPI(
            manager_url,
            username,
            password,
            allow_insecure_connections,
            tls_cacert_file
        )
        self.enclosure_group = OneViewEnclosureGroupAPI(
            manager_url,
            username,
            password,
            allow_insecure_connections,
            tls_cacert_file
        )
