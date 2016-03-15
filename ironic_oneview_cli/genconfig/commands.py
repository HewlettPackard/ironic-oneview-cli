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

import getpass
import os

from builtins import input
from configparser import ConfigParser


def generate_rc_file(file_name, **credentials):
    with open(file_name, 'w') as rc:
        for key in credentials.keys():
            value = credentials[key]
            line = "export %s=%s" % (key, value)
            rc.write(line + '\n')
            rc.truncate()


def do_genconfig(args):
    """Generates the config file according to user input

    """

    enabled_drivers = ['agent_pxe_oneview', 'iscsi_pxe_oneview']
    openstack_cacert = ''
    oneview_cacert = ''


    # OpenStack

    openstack_auth_url = input("Type the auth_url for the OpenStack service: ")
    openstack_username = input("Type your OpenStack username: ")
    openstack_tenant = input("Type your OpenStack user's tenant name: ")
    openstack_password = getpass.getpass("Type your Openstack user's password: ")
    openstack_insecure = input("Would you like to allow insecure connections "
                               "to OpenStack? [y/N]: ") or "N"
    openstack_ironic_deploy_kernel_uuid = input("Type in the default deploy "
                                                "keynel image ID on Glance: ")
    openstack_ironic_deploy_ramdisk_uuid = input("Type in the default deploy "
                                                 "ramdisk image ID on Glance: ")
    openstack_ironic_node_driver = input(("Which driver would you like to use? "
                                          "[%s]: ") % ','.join(enabled_drivers))
    openstack_insecure = 'True' if openstack_insecure.lower() == 'y' else 'False'

    if not openstack_insecure:
        openstack_cacert = input("Type the path to the OpenStack ca_file: ")


    # OneView

    oneview_manager_url = input("Type in the OneView uri: ")
    oneview_username = input("Type your OneView username: ")
    oneview_password = getpass.getpass("Type your OneView user's password: ")
    oneview_insecure = input("Would you like to allow insecure connections "
                             "to OneView? [y/N]: ") or "N"
    oneview_insecure = 'True' if oneview_insecure.lower() == 'y' else 'False'

    if not oneview_insecure:
        oneview_cacert = input("Type the path to the OneView ca_file: ")

    filename = input("Type the path to the new configuration file [%s]: "
                     % args.config_file) or args.config_file
    real_path = os.path.expanduser(filename)
    fullname = os.path.realpath(os.path.expanduser(filename))
    directory = os.path.dirname(fullname)
    if not os.path.exists(directory):
        os.makedirs(directory)

    credentials = dict()
    credentials['OS_USERNAME'] = openstack_username
    credentials['OS_PASSWORD'] = openstack_password
    credentials['OS_PROJECT_NAME'] = openstack_tenant
    credentials['OS_TENANT_NAME'] = credentials['OS_PROJECT_NAME']
    credentials['OS_CACERT'] = openstack_cacert
    credentials['OS_AUTH_URL'] = openstack_auth_url
    credentials['OS_IRONIC_DEPLOY_KERNEL_UUID'] = openstack_ironic_deploy_kernel_uuid
    credentials['OS_IRONIC_DEPLOY_RAMDISK_UUID'] = openstack_ironic_deploy_ramdisk_uuid
    credentials['OS_IRONIC_NODE_DRIVER'] = openstack_ironic_node_driver
    credentials['OV_URL'] = oneview_manager_url
    credentials['OV_USERNAME'] = oneview_username
    credentials['OV_PASSWORD'] = oneview_password
    credentials['OV_CACERT'] = oneview_cacert
    generate_rc_file('ironic-oneviewrc', **credentials)
