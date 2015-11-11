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
from keystoneclient.v2_0 import client as ksclient
from novaclient import client as nova_client

from ironic_oneview_cli import service_logging as logging


LOG = logging.getLogger(__name__)

IRONIC_API_VERSION = '1.11'


# DEPRECATED: Waiting fix on bug
# https://bugs.launchpad.net/python-ironicclient/+bug/1513481
def get_keystone_client(**kwargs):
    """Get an endpoint and auth token from Keystone.

    :param kwargs: keyword args containing credentials:
            * username: name of user
            * password: user's password
            * auth_url: endpoint to authenticate against
            * insecure: allow insecure SSL (no cert verification)
            * tenant_{name|id}: name or ID of tenant
    """
    return ksclient.Client(username=kwargs.get('username'),
                           password=kwargs.get('password'),
                           tenant_id=kwargs.get('tenant_id'),
                           tenant_name=kwargs.get('tenant_name'),
                           auth_url=kwargs.get('auth_url'),
                           insecure=kwargs.get('insecure'),
                           cacert=kwargs.get('ca_cert'))


def get_endpoint(client, **kwargs):
    """Get an endpoint using the provided keystone client."""
    attr = None
    filter_value = None
    if kwargs.get('region_name'):
        attr = 'region'
        filter_value = kwargs.get('region_name')
    return client.service_catalog.url_for(
        service_type=kwargs.get('service_type') or 'baremetal',
        attr=attr,
        filter_value=filter_value,
        endpoint_type=kwargs.get('endpoint_type') or 'publicURL')

def _is_string_equals_true(string):
    return string.lower() == 'true'

def get_ironic_client(conf):
    insecure = _is_string_equals_true(conf.ironic.insecure)
    endpoint_type = 'publicURL'
    service_type = 'baremetal'

    ks_kwargs = {
        'username': conf.ironic.admin_user,
        'password': conf.ironic.admin_password,
        'tenant_name': conf.ironic.admin_tenant_name,
        'auth_url': conf.ironic.auth_url,
        'service_type': service_type,
        'endpoint_type': endpoint_type,
        'insecure': insecure,
        'ca_cert': conf.ironic.ca_file,
    }
    ksclient = get_keystone_client(**ks_kwargs)
    token = ksclient.auth_token
    endpoint = get_endpoint(ksclient, **ks_kwargs)
    auth_ref = ksclient.auth_ref

    cli_kwargs = {
        'token': token,
        'auth_ref': auth_ref,
    }

    cli_kwargs['insecure'] = insecure
    cli_kwargs['ca_cert'] = conf.ironic.ca_file
    cli_kwargs['os_ironic_api_version'] = IRONIC_API_VERSION

    return ironic_client.Client(1, endpoint, **cli_kwargs)

def get_nova_client(conf):
    insecure = _is_string_equals_true(conf.nova.insecure)
    ca_file = conf.nova.ca_file if conf.nova.ca_file else None
    LOG.debug("Using OpenStack credentials specified in the configuration file"
              " to get Nova Client")
    nova = nova_client.Client(2, username=conf.nova.username,
                              api_key=conf.nova.password,
                              project_id=conf.nova.tenant_name,
                              auth_url=conf.nova.auth_url,
                              insecure=insecure,
                              cacert=ca_file)
    return nova
