# Copyright 2017 Hewlett Packard Enterprise Development LP
# Copyright 2017 Universidade Federal de Campina Grande
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

import argparse
import mock
import unittest

from oslo_utils import importutils

from ironic_oneview_cli import common
from ironic_oneview_cli import exceptions

hponeview_client = importutils.try_import('hpOneView.oneview_client')


class TestUtils(unittest.TestCase):
    def setUp(self):
        self.args = argparse.Namespace(
            ov_auth_url='https://1.2.3.4',
            ov_username='user',
            ov_password='password',
            ov_insecure='False',
            ov_cacert='ca_file'
        )

    @mock.patch.object(hponeview_client, 'OneViewClient', autospec=True)
    def test_get_hponeview_client(self, mock_hponeview_client):
        common.get_hponeview_client(self.args)
        config = {
            "ip": 'https://1.2.3.4',
            "credentials": {
                "userName": 'user',
                "password": 'password'
            },
            "ssl_certificate": 'ca_file'
        }
        mock_hponeview_client.assert_called_once_with(config)

    def test_get_hponeview_client_cafile_none(self):
        self.args.ov_cacert = None
        self.assertRaises(
            exceptions.OneViewConnectionError,
            common.get_hponeview_client,
            self.args
        )

    @mock.patch.object(hponeview_client, 'OneViewClient', autospec=True)
    def test_get_hponeview_client_insecure_cafile(self, mock_oneview):
        self.args.ov_insecure = 'True'
        config = {
            "ip": 'https://1.2.3.4',
            "credentials": {
                "userName": 'user',
                "password": 'password'
            },
            "ssl_certificate": None
        }
        common.get_hponeview_client(self.args)
        mock_oneview.assert_called_once_with(config)
