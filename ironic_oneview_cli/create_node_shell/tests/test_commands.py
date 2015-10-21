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

from service.create_node_shell import commands
from service.create_node_shell import create_service
import service.service_manager as service_manager
from service import objects

import mock
import requests
import unittest


class FakeElement:
    id = None


class FakeNodeManager:

    fake_node = {
        'id': 123,
        'uuid': '000000000000',
        'chassis_uuid': 'cccccccccccc',
        'maintenance': False,
        'provision_state': 'available',
        'driver': 'fake',
        'driver_info': {'server_hardware_uri': '/any/uri'},
        'name': 'fake-node-1',
        'extra': {}
    }

    def list():
        return [fake_node]

    def get(node_uuid):
        return fake_node


class FakeIronicClient:

    def __init__(self):
        self.node = FakeNodeManager()


class CreateNodesCommandsTestCase(unittest.TestCase):

    @mock.patch('__builtin__.raw_input', return_value='1 2 3')
    def test__print_prompt_ok(self, mock_raw_input):
         obj_list = []
         header_list = ['enclosureGroupName', 'serverHardwareTypeName']
         mixed_case_list = ['enclosureGroupName', 'serverHardwareTypeName']
         func_return = commands.print_prompt(
             obj_list, header_list, mixed_case_list, "Prompt message >"
         )

         self.assertEqual('1 2 3', func_return)


    @mock.patch.object(commands, '_get_element_by_id')
    def test__is_entry_invalid_true(self, mock_get_element):
        mock_get_element.return_value = None
        entries = ['invalid', 'invalid entry']

        self.assertTrue(commands.is_entry_invalid(entries, []))


    @mock.patch.object(commands, '_get_element_by_id')
    def test__is_entry_invalid_false(self, mock_get_element):
        mock_get_element.return_value = '1'
        entries = ['2', '1']
        objects_list = []

        self.assertFalse(commands.is_entry_invalid(entries, objects_list))


    def test__get_nonexistent_element_by_id(self):
        element_one = FakeElement()
        element_one.id = 1
        element_two = FakeElement()
        element_two.id = 2
        element_list = [element_one, element_two]
        nonexistent_id = 3

        self.assertIsNone(commands._get_element_by_id(element_list,
                                                      nonexistent_id))


    def test__get_valid_element_by_id(self):
        element_one = FakeElement()
        element_one.id = 1
        existent_id = 1
        returned_element = commands._get_element_by_id([element_one],
                                                       existent_id)
        self.assertIsNotNone(returned_element)
        self.assertEqual(existent_id, returned_element.id)


    @mock.patch.object(service_manager, 'get_ironic_client')
    def test__get_server_hardware_objects_not_in_ironic_ok(self, mock_get_ironic_client):
        mock_get_ironic_client.return_value = FakeIronicClient()
        server_hardware_dict = {
            'cpu_arch': 'x86_64',
            'serverGroupUri': '/any/serverGroupUri',
            'serverHardwareTypeUri': '/any/serverHardwareTypeUri',
            'cpus': 8,
            'uri': '/any/serverHardwareUri',
            'memoryMb': 32768,
            'local_gb': 100,
        }
        server_hardware_obj = objects.ServerHardware(1, server_hardware_dict)
        server_hardware_obj_2 = objects.ServerHardware(2, server_hardware_dict)
        server_hardware_objects = [server_hardware_obj, server_hardware_obj_2]
        
        returned_server_hardware_objects_not_in_ironic = commands \
            ._get_server_hardware_objects_not_in_ironic(server_hardware_objects)
        
        self.assertIsNotNone(returned_server_hardware_objects_not_in_ironic)
        self.assertEquals(2, len(returned_server_hardware_objects_not_in_ironic))
         
               
    @mock.patch.object(commands, 'print_prompt')
    def test__select_server_profile_template_input_q(self, mock_prompt):
        mock_prompt.return_value = 'q'
        server_profile_list = []

        self.assertRaises(
            SystemExit, 
            commands.select_server_profile_template,
            server_profile_list
        )


    @mock.patch.object(commands, 'print_prompt')
    def test__select_server_profile_template_ok(self, mock_prompt):
        mock_prompt.return_value = '1'
        element_one = FakeElement()
        element_one.id = 1
        returned_server_profile_template = commands.select_server_profile_template([element_one])

        self.assertIsNotNone(returned_server_profile_template)
        self.assertEqual(element_one.id, returned_server_profile_template.id)


    @mock.patch.object(commands, 'print_prompt')
    def test__select_server_hardware_objects_input_q(self, mock_prompt):
        mock_prompt.return_value = 'q'
        server_hardware_list = []

        self.assertRaises(
            SystemExit, 
            commands.select_server_hardware_objects,
            server_hardware_list
        )


    @mock.patch.object(commands, 'print_prompt')
    def test__select_one_server_hardware_object(self, mock_prompt):
        mock_prompt.return_value = '1'
        element_one = FakeElement()
        element_one.id = 1
        returned_server_hardware = commands.select_server_profile_template([element_one])

        self.assertIsNotNone(returned_server_hardware)
        self.assertEqual(element_one.id, returned_server_hardware.id)


    @mock.patch.object(commands, 'print_prompt')
    @mock.patch.object(commands, 'is_entry_invalid')
    def test__select_more_than_one_server_hardware_objects(self, mock_entry_invalid, mock_prompt):
        mock_entry_invalid.return_value = False
        mock_prompt.return_value = '1 2'
        element_one = FakeElement()
        element_one.id = 1
        element_two = FakeElement()
        element_two.id = 2
        server_hardware_list = [element_one, element_two]
        returned_server_hardware_list = commands.select_server_hardware_objects(server_hardware_list)

        self.assertIsNotNone(returned_server_hardware_list)
        self.assertEqual(2, len(returned_server_hardware_list))
        self.assertEqual(element_one.id, int(returned_server_hardware_list[0]))
        self.assertEqual(element_two.id, int(returned_server_hardware_list[1]))
 

if __name__ == '__main__':
    unittest.main()
