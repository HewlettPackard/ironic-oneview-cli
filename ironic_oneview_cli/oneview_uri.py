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

AUTHENTICATION_URL = '/rest/login-sessions'
SERVER_PROFILE_LIST_URI = '/rest/server-profile-templates?start=0&count=-1'
SERVER_HARDWARE_LIST_URI = '/rest/server-hardware?filter="status=Disabled OR'
'status=OK OR status=Warning"'
VOLUMES_URI = '/rest/storage-volumes?start=0&count=-1'

CERTIFICATE_RABBIT_MQ = '/rest/certificates/client/rabbitmq'
CERTIFICATE_AND_KEY_URI = "/rest/certificates/client/rabbitmq/keypair/default"
CA_URI = "/rest/certificates/ca"
