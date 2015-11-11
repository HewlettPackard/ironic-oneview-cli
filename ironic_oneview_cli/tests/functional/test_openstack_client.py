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
test_openstack_client
----------------------------------

Tests for `openstack_client.py` module.
"""

import unittest

from ironic_oneview_cli.config import ConfClient
from ironic_oneview_cli import openstack_client


TEST_CONFIG_FOLDER = 'ironic_oneview_cli/tests/'

TEST_CONFIG_PATH_IRONIC_SECURE_WITH_CA =\
    TEST_CONFIG_FOLDER +\
    'ironic-oneview-cli-tests-ironic-secure-with-ca-file.conf'

TEST_CONFIG_PATH_IRONIC_SECURE_WITHOUT_CA =\
    TEST_CONFIG_FOLDER +\
    'ironic-oneview-cli-tests-ironic-secure-without-ca-file.conf'

TEST_CONFIG_PATH_IRONIC_INSECURE =\
    TEST_CONFIG_FOLDER + 'ironic-oneview-cli-tests-ironic-insecure.conf'

TEST_CONFIG_PATH_NOVA_SECURE_WITH_CA =\
    TEST_CONFIG_FOLDER +\
    'ironic-oneview-cli-tests-nova-secure-with-ca-file.conf'

TEST_CONFIG_PATH_NOVA_SECURE_WITHOUT_CA =\
    TEST_CONFIG_FOLDER +\
    'ironic-oneview-cli-tests-nova-secure-without-ca-file.conf'

TEST_CONFIG_PATH_NOVA_INSECURE =\
    TEST_CONFIG_FOLDER + 'ironic-oneview-cli-tests-nova-insecure.conf'


class TestOpenStackClient(unittest.TestCase):
    def setUp(self):
        defaults = {
            "ca_file": "",
            "insecure": False,
            "tls_cacert_file": "",
            "allow_insecure_connections": False,
        }
        self.config_ironic_secure_with_ca = ConfClient(
            TEST_CONFIG_PATH_IRONIC_SECURE_WITH_CA, defaults)
        self.config_ironic_secure_without_ca = ConfClient(
            TEST_CONFIG_PATH_IRONIC_SECURE_WITHOUT_CA, defaults)
        self.config_ironic_insecure = ConfClient(
            TEST_CONFIG_PATH_IRONIC_INSECURE, defaults)

        self.config_nova_secure_with_ca = ConfClient(
            TEST_CONFIG_PATH_NOVA_SECURE_WITH_CA, defaults)
        self.config_nova_secure_without_ca = ConfClient(
            TEST_CONFIG_PATH_NOVA_SECURE_WITHOUT_CA, defaults)
        self.config_nova_insecure = ConfClient(
            TEST_CONFIG_PATH_NOVA_INSECURE, defaults)

    def test_secure_ironic_passing_ca_cert(self):
        config = self.config_ironic_secure_with_ca
        openstack_client.get_ironic_client(config)

    def test_secure_ironic_without_passing_ca_cert(self):
        config = self.config_ironic_secure_without_ca
        with self.assertRaises(Exception):
            openstack_client.get_ironic_client(config)

    def test_insecure_ironic(self):
        config = self.config_ironic_insecure
        openstack_client.get_ironic_client(config)

    def test_secure_nova_passing_ca_cert(self):
        config = self.config_nova_secure_with_ca
        client = openstack_client.get_nova_client(config)
        self.assertIs(type(client.servers.list()), list)

    def test_secure_nova_without_passing_ca_cert(self):
        config = self.config_nova_secure_without_ca
        client = openstack_client.get_nova_client(config)
        with self.assertRaises(Exception):
            client.servers.list()

    def test_insecure_nova(self):
        config = self.config_nova_insecure
        client = openstack_client.get_nova_client(config)
        self.assertIs(type(client.servers.list()), list)


if __name__ == '__main__':
    unittest.main()
