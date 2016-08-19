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

from builtins import input

from ironic_oneview_cli import facade
from ironic_oneview_cli.openstack.common import cliutils


class NodeDelete(object):

    def __init__(self, facade_cli):
        self.facade = facade_cli

    def delete_ironic_nodes(self, number=None):
        nodes = self.facade.get_ironic_node_list()
        if number:
            for n in range(number):
                try:
                    self.facade.node_delete(nodes[n].uuid)
                except Exception as e:
                    print(e.message)
        else:
            for node in nodes:
                try:
                    self.facade.node_delete(node.uuid)
                except Exception as e:
                    print(e.message)


@cliutils.arg(
    '--all',
    action='store_true',
    help='Delete all ironic nodes'
)
@cliutils.arg(
    '-n', '--number',
    metavar='<number>',
    type=int,
    help='Delete multiple ironic nodes'
)
def do_node_delete(args):
    """Delete nodes in Ironic"""

    node_delete = NodeDelete(facade.Facade(args))

    if args.all:
        while True:
            response = input('Do you really want to delete all nodes? [y/N] ')
            if response.lower() == 'n' or not response:
                break
            elif response.lower() == 'y':
                node_delete.delete_ironic_nodes()
                print('Nodes deleted')
                break
            else:
                print('Invalid option')
    elif args.number:
        node_delete.delete_ironic_nodes(args.number)
        print(('%(nodes_number)s nodes deleted') %
              {'nodes_number': args.number})
    else:
        print("Not implemented")
