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

from oslo_utils import importutils

client = importutils.try_import('oneview_client.client')
oneview_utils = importutils.try_import('oneview_client.utils')

SUPPORTED_DRIVERS = [
    'agent_pxe_oneview',
    'iscsi_pxe_oneview',
    'fake_oneview'
]


def get_oneview_client(manager_url, username, password,
                       allow_insecure_connections=False, tls_cacert_file='',
                       polling_timeout=20):
    """Generates an instance of the OneView client.

    Generates an instance of the OneView client using the imported
    oneview_client library.

    :returns: an instance of the OneView client
    """

    oneview_client = client.ClientV2(
        manager_url=manager_url,
        username=username,
        password=password,
        allow_insecure_connections=allow_insecure_connections,
        tls_cacert_file=tls_cacert_file,
        max_polling_attempts=polling_timeout
    )
    return oneview_client
