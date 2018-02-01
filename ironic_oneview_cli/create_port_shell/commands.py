# Copyright (2015-2017) Hewlett Packard Enterprise Development LP.
# Copyright (2015-2017) Universidade Federal de Campina Grande
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

from ironic_oneview_cli import common
from ironic_oneview_cli import exceptions
from ironic_oneview_cli import facade


class PortCreator(object):
    def __init__(self, port_facade):
        self.facade = port_facade

    def create_port(self, args, ironic_node):
        server_hardware_uri = ironic_node.driver_info.get(
            "server_hardware_uri")
        server_hardware = self.facade.get_server_hardware(server_hardware_uri)

        if args.mac:
            mac = args.mac
        else:
            mac = self.get_server_hardware_mac(server_hardware)

        if not self.validate_server_hardware_mac(mac, server_hardware):
            print(("WARNING: mac %(mac)s doesn't match any server "
                   "hardware's %(sh)s ports.\n"
                   "Use ironic-oneview port-create command with a valid MAC "
                   "address to create an Ironic Port for this Ironic Node.") %
                  {"mac": mac, "sh": server_hardware.get('uuid')})
            return None

        self.verifify_existing_ports_for_node(ironic_node)

        attrs = common.create_attrs_for_port(ironic_node, mac)
        return self.facade.create_ironic_port(**attrs)

    def validate_server_hardware_mac(self, mac, server_hardware):
        """Validate if MAC exists for Server Hardware.

        Verify if a MAC matches any Physical or Virtual MAC of a
        Server Hardware.

        :param mac: The MAC Address to be validated.
        :param server_hardware: The Server Hardware used for the validation.
        :returns: Wether it is a valid MAC or not.
        """
        physical_and_virtual_macs = []
        port_map = server_hardware.get('portMap', {})
        if port_map is not None:
            for device in port_map.get('deviceSlots', ()):
                for physical_port in device.get('physicalPorts', ()):
                    if physical_port.get('type') == 'Ethernet':
                        mac_address = physical_port.get('mac', '').lower()
                        physical_and_virtual_macs.append(mac_address)
                        for virtual_port in physical_port.get(
                                'virtualPorts', ()):
                            mac_address = virtual_port.get('mac', '').lower()
                            physical_and_virtual_macs.append(mac_address)
        else:
            ilo_mac = self.facade.get_server_hardware_mac_from_ilo(
                server_hardware)
            physical_and_virtual_macs = [ilo_mac.lower()]
        return mac.lower() in physical_and_virtual_macs

    def get_server_hardware_mac(self, server_hardware):
        if not server_hardware.get('portMap'):
            return self.facade.get_server_hardware_mac_from_ilo(
                server_hardware)

        sh_physical_port = common.get_first_ethernet_physical_port(
            server_hardware)
        if sh_physical_port:
            for virtual_port in sh_physical_port.get('virtualPorts'):
                # NOTE(nicodemos): Ironic oneview drivers needs to use a
                # port that type is Ethernet and function 'a' to be able
                # to peform a deploy.
                if virtual_port.get('portFunction') == 'a':
                    return virtual_port.get('mac').lower()
            return None
        raise exceptions.OneViewResourceNotFoundError(
            "There is no Ethernet port on the Server Hardware: %s"
            % server_hardware.get('uri'))

    def verifify_existing_ports_for_node(self, ironic_node):
        ironic_ports = self.facade.get_ironic_port_list()
        ports = [port for port in ironic_ports if
                 port.node_uuid == ironic_node.uuid]
        if ports:
            print("There are created ports for this node already. The CLI "
                  "will try to create it as another port.")


@common.arg(
    'node',
    metavar='<node_uuid>',
    help='Create a port based on a given ironic node uuid.')
@common.arg(
    '-m', '--mac',
    help='MAC Address of the HPE OneView Server Hardware.')
def do_port_create(args):
    """Create port based on a Ironic Node.

    If not specified, it retrieves the mac address of the first '-a' available
    port at the Server Hardware to which the Ironic Node is related to. It
    also gathers the local link connection if the Ironic Node is enabled to
    use the OneView ml2 driver.
    """
    facade_obj = facade.Facade(args)
    port_creator = PortCreator(facade_obj)

    ironic_node = facade_obj.get_ironic_node(args.node)
    port = port_creator.create_port(args, ironic_node)

    if port:
        print("Created port %s" % port.uuid)
