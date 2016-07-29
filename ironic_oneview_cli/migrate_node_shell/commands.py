# -*- encoding: utf-8 -*-
#
# Copyright 2016 Hewlett Packard Enterprise Development LP.
# Copyright 2016 Universidade Federal de Campina Grande
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

import sys

from builtins import input

from ironic_oneview_cli import common
from ironic_oneview_cli import facade
from ironic_oneview_cli.openstack.common import cliutils
from ironic_oneview_cli import service_logging as logging

LOG = logging.getLogger(__name__)
NODE_MIGRATING_TO_DYNAMIC_ALLOCATION = 'Migrating to dynamic allocation'


class NodeMigrator(object):
    def __init__(self, facade_cli):
        self.facade = facade_cli

    def list_pre_allocation_nodes(self):
        pre_allocation_nodes = filter(
            lambda x: x.driver in common.SUPPORTED_DRIVERS
            and x.driver_info.get('dynamic_allocation')
            in (None, False, 'False')
            or x.maintenance_reason == NODE_MIGRATING_TO_DYNAMIC_ALLOCATION,
            self.facade.get_ironic_node_list()
        )

        return pre_allocation_nodes

    def filter_nodes_by_state(self, pre_allocation_nodes_list):
        pre_allocation_nodes_allow_to_migrate = []
        for node in pre_allocation_nodes_list:
            if node.provision_state in ('enroll', 'manageable', 'available',
                                        'active', 'inspect failed',
                                        'clean failed', 'error'):
                pre_allocation_nodes_allow_to_migrate.append(node)
            else:
                message = ("The following node is not in a state available"
                           "to migrate: %s" % (node.uuid))
                LOG.warn(message)

        return pre_allocation_nodes_allow_to_migrate

    def update_nodes_with_oneview_fields(self, pre_allocation_nodes_list):
        nodes_updated = []

        for node in pre_allocation_nodes_list:
            node_server_hardware_uri = node.driver_info.get(
                'server_hardware_uri'
            )

            server_hardware = self.facade.get_server_hardware(
                node_server_hardware_uri
            )

            enclosure_group = self.facade.get_enclosure_group(
                server_hardware.enclosure_group_uri
            )

            server_hardware_type = self.facade.get_server_hardware_type(
                server_hardware.server_hardware_type_uri
            )

            node.server_hardware_name = server_hardware.name
            node.server_profile_uri = server_hardware.server_profile_uri
            node.server_hardware_type_name = server_hardware_type.name
            node.enclosure_group_name = enclosure_group.name

            nodes_updated.append(node)

        return nodes_updated

    def get_ironic_nodes_by_uuid(self, list_nodes_uuid):
        list_nodes_to_migrate = []
        for node_uuid in list_nodes_uuid:
            try:
                node = self.facade.get_ironic_node(node_uuid)
                if self.is_node_in_dynamic_allocation(node) is False:
                    list_nodes_to_migrate.append(node)
            except Exception as e:
                print(e.message)

        return list_nodes_to_migrate

    def is_node_in_dynamic_allocation(self, node):
        if node.driver_info.get('dynamic_allocation') \
                in (None, False, 'False'):
            return False
        else:
            if node.maintenance_reason == NODE_MIGRATING_TO_DYNAMIC_ALLOCATION:
                self.facade.node_set_maintenance(
                    node.uuid,
                    False,
                    ''
                )

            message = ("The following node is already in the "
                       "dynamic allocation model: %s" % (node.uuid))
            LOG.warn(message)

            return True

    def verify_nodes_with_instances_and_migrate(self, nodes_to_migrate):
        for node in nodes_to_migrate:
            if node.instance_uuid:
                self.migrate_node_with_instance(node)
            else:
                self.migrate_idle_node(node)

    def migrate_idle_node(self, node_to_migrate):
        maintenance_reason = NODE_MIGRATING_TO_DYNAMIC_ALLOCATION
        add_dynamic_flag = [{'op': 'add',
                             'path': '/driver_info/dynamic_allocation',
                             'value': True}]

        self.facade.node_set_maintenance(
            node_to_migrate.uuid,
            True,
            maintenance_reason
        )

        try:
            self.facade.delete_server_profile(
                node_to_migrate.server_profile_uri
            )
        # NOTE(nicodemos): Ignore in case the operation fails because
        # there is not a server profile;
        except ValueError:
            pass
        except Exception as e:
            print(e.message)

        self.facade.node_update(
            node_to_migrate.uuid,
            add_dynamic_flag
        )
        self.facade.node_set_maintenance(
            node_to_migrate.uuid,
            False,
            ''
        )

    def migrate_node_with_instance(self, node_to_migrate):
        if self.is_node_in_dynamic_allocation(node_to_migrate) is False:
            add_dynamic_flag = [
                {'op': 'add',
                 'path': '/driver_info/dynamic_allocation',
                 'value': True}
            ]
            add_applied_server_profile = [
                {'op': 'add',
                 'path': '/driver_info/'
                         'applied_server_profile_uri',
                 'value':
                         node_to_migrate.server_profile_uri}
            ]
            self.facade.node_update(
                node_to_migrate.uuid,
                add_applied_server_profile + add_dynamic_flag
            )


def print_prompt(object_list, header_list, input_message=None,
                 field_labels=None):
    cliutils.print_list(
        object_list,
        header_list,
        mixed_case_fields=[],
        field_labels=field_labels
    )
    if input_message is not None:
        input_value = input(input_message)
        return input_value


def assign_elements_with_new_id(element_list):
    counter = 1
    for element in element_list:
        element.id = counter
        counter += 1


def get_element_by_id(element_list, element_id):
    try:
        for element in element_list:
            if element.id == int(element_id):
                return element
    except Exception:
        return None


def is_entry_invalid(entries, objects_list):
    for entry in entries:
        element = get_element_by_id(objects_list, entry)
        if element is None:
            return True
    return False


@cliutils.arg(
    '--all',
    action='store_true',
    help="Migrate all pre-allocation nodes to dynamic allocation")
@cliutils.arg(
    '--nodes',
    nargs='+',
    help="UUID of the nodes you want to migrate.")
def do_migrate_to_dynamic(args):
    """Migrate nodes from pre-allocation to dynamic allocation model."""

    node_migrator = NodeMigrator(facade.Facade(args))

    if args.all:
        pre_allocation_nodes = \
            node_migrator.list_pre_allocation_nodes()
        nodes_allow_to_migrate = \
            node_migrator.filter_nodes_by_state(
                pre_allocation_nodes
            )
        nodes_oneview_fields = \
            node_migrator.update_nodes_with_oneview_fields(
                nodes_allow_to_migrate
            )
        node_migrator.verify_nodes_with_instances_and_migrate(
            nodes_oneview_fields
        )

        print("All pre-allocation nodes migrated to dynamic allocation!\n")
    elif args.nodes:
        nodes_to_migrate = node_migrator.get_ironic_nodes_by_uuid(args.nodes)
        nodes_allow_to_migrate = \
            node_migrator.filter_nodes_by_state(nodes_to_migrate)
        nodes_oneview_fields = \
            node_migrator.update_nodes_with_oneview_fields(
                nodes_allow_to_migrate
            )

        if nodes_oneview_fields:
            node_migrator.verify_nodes_with_instances_and_migrate(
                nodes_oneview_fields
            )

            print('Migration complete.\n')
    else:
        print("Retrieving pre-allocation Nodes from Ironic...")
        migrate_another_node_flag = True
        while migrate_another_node_flag:
            migrate_another_node_flag = False

            pre_allocation_nodes = \
                node_migrator.list_pre_allocation_nodes()
            nodes_allow_to_migrate = \
                node_migrator.filter_nodes_by_state(
                    pre_allocation_nodes
                )
            nodes_oneview_fields = \
                node_migrator.update_nodes_with_oneview_fields(
                    nodes_allow_to_migrate
                )

            assign_elements_with_new_id(nodes_oneview_fields)
            invalid_pre_allocation_node = True
            while invalid_pre_allocation_node:
                input_id = print_prompt(
                    nodes_oneview_fields,
                    [
                        'id',
                        'uuid',
                        'server_hardware_name',
                        'server_hardware_type_name',
                        'enclosure_group_name'
                    ],
                    input_message="Enter a space separated list of "
                    "pre-allocation nodes Id's you want to migrate. "
                    "e.g. 1 2 3. ('all' to migrate all nodes or "
                    "'q' to quit)> ",
                    field_labels=[
                        'Id',
                        'Node UUID',
                        'Server Hardware Name',
                        'Server Hardware Type Name',
                        'Enclosure Group Name'
                    ]
                )
                if input_id == 'all':
                    node_migrator.verify_nodes_with_instances_and_migrate(
                        nodes_oneview_fields
                    )

                    print("All pre-allocation nodes migrated "
                          "to dynamic allocation!\n")
                    sys.exit()

                if input_id == 'q':
                    sys.exit()

                pre_allocation_nodes_selected = input_id.split()
                invalid_pre_allocation_node = is_entry_invalid(
                    pre_allocation_nodes_selected, nodes_oneview_fields
                )

                for node_id in pre_allocation_nodes_selected:
                    node_selected = get_element_by_id(
                        nodes_oneview_fields,
                        node_id
                    )

                    print("\nMigrating the following pre-allocation Node: ")
                    cliutils.print_list(
                        [node_selected],
                        ['uuid', 'server_hardware_name',
                         'server_hardware_type_name', 'enclosure_group_name'],
                        field_labels=[
                            'Node UUID',
                            'Server Hardware Name',
                            'Server Hardware Type Name',
                            'Enclosure Group Name'
                        ]
                    )

                    node_migrator.verify_nodes_with_instances_and_migrate(
                        [node_selected]
                    )

                    print('Node migrated!\n')

            while True:
                response = input(
                    'Would you like to migrate another Node? [y/N] '
                )
                if response.lower() == 'n' or not response:
                    migrate_another_node_flag = False
                    break
                elif response == 'y':
                    migrate_another_node_flag = True
                    break
                else:
                    print('Invalid option')
