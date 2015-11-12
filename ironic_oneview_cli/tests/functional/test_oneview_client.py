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

"""
test_oneview_client
----------------------------------

Tests for `oneview_client.py` module.
"""

import unittest

from ironic_oneview_cli.config import ConfClient
from ironic_oneview_cli import oneview_client


TEST_CONFIG_FOLDER = 'ironic_oneview_cli/tests/'

TEST_CONFIG_PATH_ONEVIEW_SECURE_WITH_CA =\
    TEST_CONFIG_FOLDER +\
    'ironic-oneview-cli-tests-oneview-secure-with-ca-file.conf'

TEST_CONFIG_PATH_ONEVIEW_SECURE_WITHOUT_CA =\
    TEST_CONFIG_FOLDER +\
    'ironic-oneview-cli-tests-oneview-secure-without-ca-file.conf'

TEST_CONFIG_PATH_ONEVIEW_INSECURE =\
    TEST_CONFIG_FOLDER +\
    'ironic-oneview-cli-tests-oneview-insecure.conf'


class TestOneViewClient(unittest.TestCase):
    def setUp(self):
        defaults = {
            "ca_file": "",
            "insecure": False,
            "tls_cacert_file": "",
            "allow_insecure_connections": False,
        }
        self.config_oneview_secure_with_ca = ConfClient(
            TEST_CONFIG_PATH_ONEVIEW_SECURE_WITH_CA, defaults)
        self.config_oneview_secure_without_ca = ConfClient(
            TEST_CONFIG_PATH_ONEVIEW_SECURE_WITHOUT_CA, defaults)
        self.config_oneview_insecure = ConfClient(
            TEST_CONFIG_PATH_ONEVIEW_INSECURE, defaults)

    def test_list_server_hardware_in_secure_oneview_passing_ca_cert(self):
        config = self.config_oneview_secure_with_ca
        client = oneview_client.get_oneview_client(config)
        self.assertIs(type(client.server_hardware.list()), list)

    def test_list_server_hardware_in_secure_oneview_without_ca_cert(self):
        config = self.config_oneview_secure_without_ca
        client = oneview_client.get_oneview_client(config)
        with self.assertRaises(Exception):
            client.server_hardware.list()

    def test_list_server_hardware_in_insecure_oneview(self):
        config = self.config_oneview_insecure
        client = oneview_client.get_oneview_client(config)
        self.assertIs(type(client.server_hardware.list()), list)


if __name__ == '__main__':
    unittest.main()
