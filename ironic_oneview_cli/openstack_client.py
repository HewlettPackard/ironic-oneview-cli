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

from ironicclient import client as ironic_client
from novaclient import client as nova_client

from ironic_oneview_cli import service_logging as logging


LOG = logging.getLogger(__name__)

IRONIC_API_VERSION = '1.11'


def get_ironic_client(conf):
    kwargs = {
        'os_username': conf.ironic.admin_user,
        'os_password': conf.ironic.admin_password,
        'os_auth_url': conf.ironic.auth_url,
        'os_tenant_name': conf.ironic.admin_tenant_name,
        'os_ironic_api_version': IRONIC_API_VERSION,
    }
    if conf.ironic.insecure.lower() == 'true':
        kwargs['insecure'] = True
    if conf.ironic.ca_file:
        kwargs['ca_file'] = conf.ironic.ca_file

    LOG.debug("Using OpenStack credentials specified in the configuration file"
              " to get Ironic Client")
    ironicclient = ironic_client.get_client(1, **kwargs)
    return ironicclient


def get_nova_client(conf):
    kwargs = {
        'auth_url': conf.nova.auth_url,
        'username': conf.nova.username,
        'password': conf.nova.password,
        'tenant_name': conf.nova.tenant_name
    }
    if conf.nova.insecure.lower() == 'true':
        kwargs['insecure'] = True
    if conf.nova.ca_file:
        kwargs['ca_file'] = conf.nova.ca_file
    else:
        kwargs['ca_file'] = None
    LOG.debug("Using OpenStack credentials specified in the configuration file"
              " to get Nova Client")
    nova = nova_client.Client(2, conf.nova.username,
                              conf.nova.password,
                              conf.nova.tenant_name,
                              conf.nova.auth_url,
                              kwargs['insecure'],
                              kwargs['ca_file'])
    return nova
