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

import commands
import unittest


class TestCommands(unittest.TestCase):

    def test_get_flavor_name(self):
        with self.assertRaises(AttributeError):
            commands._get_flavor_name(None)

        with self.assertRaises(AttributeError):
            anything = "test"
            commands._get_flavor_name(anything)

    def test_get_element_by_id(self):
        with self.assertRaises(TypeError):
            commands._get_element_by_id(None, 1)

        self.assertEquals(commands._get_element_by_id([], 1), None)

        with self.assertRaises(AttributeError):
            commands._get_element_by_id([1], 1)

    def test_get_flavor_from_ironic_node(self):
        node = Node(10, 20, 30, 'server_hardware_type_uri:any', {'server_profile_template_uri': 'any'})
        flavor = commands.get_flavor_from_ironic_node(1, node)
        self.assertEquals(flavor.cpu_arch, 'x86_64')
        self.assertEquals(flavor.cpus, 10)
        self.assertEquals(flavor.ram_mb, 20)
        self.assertEquals(flavor.disk, 30)
        self.assertEquals(flavor.id, 1)
        self.assertEquals(flavor.server_profile_template_uri, 'any')
        self.assertEquals(flavor.server_hardware_type_uri, 'any')

    def test_get_flavor_list(self):
        with self.assertRaises(AttributeError):
            commands.get_flavor_list(None)

        flavors = commands.get_flavor_list(Client())
        self.assertEquals(flavors, set([]))


class Client:
    def __init__(self):
        self.node = Node(1,1,1,None,{})
    
class Node:
    def __init__(self, cpu, mem, disk, capabilities, driver_info):
        self.properties = {}
        self.properties['cpus'] = cpu
        self.properties['memory_mb'] = mem
        self.properties['local_gb'] = disk
        self.properties['capabilities'] = capabilities
        self.driver_info = driver_info

    def list(self, detail):
        return []


if __name__ == '__main__':
    unittest.main()
