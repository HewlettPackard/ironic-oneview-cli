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

from builtins import input
from ironic_oneview_cli import common


def _generate(**data):
    bash_file = ''

    echo = 'echo "Please enter your HP OneView password: "'
    read = 'read -sr OV_PASSWORD_INPUT'
    export = 'export OV_PASSWORD=$OV_PASSWORD_INPUT'

    for key in data.keys():
        value = data[key]
        line = "export %s=%s" % (key, value)
        bash_file = bash_file + line + '\n'

    return bash_file + echo + '\n' + read + '\n' + export + '\n'


def _save(path, filename='ironic-oneviewrc.sh', **data):
    if filename in path:
        path = path.replace(filename, '')
    canonical = os.path.realpath(os.path.expanduser(path))
    directory = os.path.dirname(canonical)
    if not os.path.exists(directory):
        os.makedirs(directory)
    full_path = os.path.join(canonical, filename)
    bash = _generate(**data)
    with open(full_path, 'w') as ironic_oneviewrc:
        for line in bash:
            ironic_oneviewrc.write(line)
    return full_path


def do_genrc(args):
    """Generates the ironic-oneviewrc.sh file according to user input."""

    # OneView

    auth_url = input("HP OneView URL: ")
    username = input("HP OneView username: ")
    cacert = input("HP OneView cacert file path "
                   "(only for secure connections): ")

    # OpenStack

    ironic_deploy_kernel = input("Ironic deploy kernel image uuid: ")
    ironic_deploy_ramdisk = input("Ironic deploy ramdisk image uuid: ")
    ironic_driver = input(
        "Select an Ironic OneView driver [%s]"
        "\nDefault to agent_pxe_oneview: " %
        ', '.join(common.SUPPORTED_DRIVERS)
    )
    if ironic_driver not in common.SUPPORTED_DRIVERS:
        ironic_driver = 'agent_pxe_oneview'

    path = input("Path to save 'ironic-oneviewrc.sh' file [%s]: " %
                 os.path.join(os.getcwd(), 'ironic-oneviewrc.sh'))

    # Map Informations

    ironic_oneviewrc = dict()
    ironic_oneviewrc['OV_AUTH_URL'] = auth_url
    ironic_oneviewrc['OV_USERNAME'] = username
    ironic_oneviewrc['OV_CACERT'] = cacert
    ironic_oneviewrc['OS_IRONIC_DEPLOY_KERNEL_UUID'] = ironic_deploy_kernel
    ironic_oneviewrc['OS_IRONIC_DEPLOY_RAMDISK_UUID'] = ironic_deploy_ramdisk
    ironic_oneviewrc['OS_IRONIC_NODE_DRIVER'] = ironic_driver

    # Create ironic-oneviewrc.sh

    print('File saved in %s' % (_save(path, **ironic_oneviewrc)))
