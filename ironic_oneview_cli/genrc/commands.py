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

import os
import getpass

from builtins import input


def generate_rc_file(file_name='ironic-oneviewrc.sh', **credentials):
    password = 'echo "Please enter your HP OneView password: "'
    read_password = 'read -sr OV_PASSWORD_INPUT'
    export_password = 'export OV_PASSWORD=$OV_PASSWORD_INPUT'

    with open(file_name, 'w') as rc:
        for key in credentials.keys():
            value = credentials[key]
            line = "export %s=%s" % (key, value)
            rc.write(line + '\n')
            rc.truncate()
        rc.write(password + '\n')
        rc.write(read_password + '\n')
        rc.write(export_password + '\n')
        rc.close()


def do_genrc(args):
    """Generates the ironic-oneviewrc file according to user input.
    """

    enabled_drivers = ['agent_pxe_oneview', 'iscsi_pxe_oneview']

    # OpenStack

    openstack_ironic_deploy_kernel_uuid = input("Type in the default deploy "
                                                "keynel image UUID on Glance: ")
    openstack_ironic_deploy_ramdisk_uuid = input("Type in the default deploy "
                                                 "ramdisk image UUID on Glance: ")
    openstack_ironic_node_driver = input(("Which driver would you like to use? "
                                          "[%s]: ") % ','.join(enabled_drivers))

    # OneView

    oneview_manager_url = input("Type the HP OneView URL: ")
    oneview_username = input("Type your HP OneView username: ")
    oneview_cacert = input("Type the path to your HP OneView cacert file: ")

    # File

    filename = input("Type the path to the 'ironic-oneviewrc.sh' file: ")
    fullname = os.path.realpath(os.path.expanduser(filename))
    directory = os.path.dirname(fullname)
    if not os.path.exists(directory):
        os.makedirs(directory)

    credentials = dict()
    credentials['OS_IRONIC_DEPLOY_KERNEL_UUID'] = openstack_ironic_deploy_kernel_uuid
    credentials['OS_IRONIC_DEPLOY_RAMDISK_UUID'] = openstack_ironic_deploy_ramdisk_uuid
    credentials['OS_IRONIC_NODE_DRIVER'] = openstack_ironic_node_driver
    credentials['OV_AUTH_URL'] = oneview_manager_url
    credentials['OV_USERNAME'] = oneview_username
    credentials['OV_CACERT'] = oneview_cacert

    generate_rc_file(**credentials)
