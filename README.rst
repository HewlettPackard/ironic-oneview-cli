==================
Ironic-OneView CLI
==================

Overview
========

Ironic-OneView CLI is a command line interface tool for easing the use of the
OneView Drivers for Ironic. It allows the user to easily create and configure
Ironic nodes compatible with OneView ``Server Hardware`` objects. It also helps
create Nova flavors to match available Ironic nodes that use OneView drivers.

This tool creates Ironic nodes based on the Ironic OneView drivers' dynamic
allocation model [1]_ [2]_.

.. note::
   If you still want to use the deprecated pre-allocation model instead, use
   version 0.0.2 of this tool.

For more information on *HP OneView* entities, see [3]_.

Installation
============

To install Ironic-OneView CLI from PyPi, use the following command::

    $ pip install ironic-oneview-cli


Configuration
=============

Ironic-Oneview CLI uses credentials loaded into environment variables by
the OpenStack RC and by the Ironic-OneView CLI RC files. You can download
the OpenStack RC file from your cloud controller. The Ironic-OneView CLI RC
file can be generated using the ``genrc`` subcommand::

    $ ironic-oneview genrc

Since you have the ``ironic-oneviewrc.sh`` file, load its environment
variables by running::

    $ source ironic-oneviewrc.sh

You can also set credentials by passing them as command line parameters.
To see which parameters to use for setting credentials, use the command::

    $ ironic-oneview help

For more information how to obtain and load the *OpenStack RC* file, see [4]_.


Usage
=====

Once the necessary environment variables and command line parameters are
set, Ironic-OneView CLI is ready to be used.

Synopsis::

In the current version of Ironic-OneView CLI, the available subcommands are:

+---------------+-----------------------------------------------------------------+
|  node-create  | Creates nodes based on available HP OneView Server Hardware.    |
+---------------+-----------------------------------------------------------------+
| flavor-create | Creates flavors based on available Ironic nodes.                |
+---------------+-----------------------------------------------------------------+
|     genrc     | Generates the ironic-oneviewrc.sh file according to user input. |
+---------------+-----------------------------------------------------------------+
|     help      | Displays help about this program or one of its subcommands.     |
+---------------+-----------------------------------------------------------------+


Features
========

Node creation
^^^^^^^^^^^^^

To create Ironic nodes based on available HP OneView ``Server Hardware`` objects,
use the following command::

    $ ironic-oneview node-create

The tool will ask you to choose a valid ``Server Profile Template`` from those
retrieved from HP OneView appliance.::

    Retrieving Server Profile Templates from OneView...
    +----+------------------------+----------------------+---------------------------+
    | Id | Name                   | Enclosure Group Name | Server Hardware Type Name |
    +----+------------------------+----------------------+---------------------------+
    | 1  | template-dcs-virt-enc3 | virt-enclosure-group | BL460c Gen8 3             |
    | 2  | template-dcs-virt-enc4 | virt-enclosure-group | BL660c Gen9 1             |
    +----+------------------------+----------------------+---------------------------+

Once you have chosen a valid ``Server Profile Template``, the tool lists the
available ``Server Hardware`` that match the chosen ``Server Profile
Template``.

Choose a ``Server Hardware`` to be used as base to the
Ironic node you are creating.::

    Listing compatible Server Hardware objects...
    +----+-----------------+------+-----------+----------+----------------------+---------------------------+
    | Id | Name            | CPUs | Memory MB | Local GB | Enclosure Group Name | Server Hardware Type Name |
    +----+-----------------+------+-----------+----------+----------------------+---------------------------+
    | 1  | VIRT-enl, bay 5 | 8    | 32768     | 120      | virt-enclosure-group | BL460c Gen8 3             |
    | 2  | VIRT-enl, bay 8 | 8    | 32768     | 120      | virt-enclosure-group | BL460c Gen8 3             |
    +----+-----------------+------+-----------+----------+----------------------+---------------------------+

Notice that you can create multiple Ironic nodes at once. For that, type
multiple ``Server Hardware`` IDs separated by blank spaces. The created Ironic
nodes will be in the *enroll* provisioning state.

To list all nodes in Ironic, use the command::

    $ ironic node-list

For more information about the created Ironic node, use the command::

    $ ironic node-show [NODE_UUID]


Flavor creation
^^^^^^^^^^^^^^^

To create Nova flavors compatible with available Ironic nodes, use the
following command::

    $ ironic-oneview flavor-create

The tool will now prompt you to choose a valid flavor configuration, according
to available Ironic nodes.::

    +----+------+---------+-----------+-------------------------------------+----------------------+-------------------------+
    | Id | CPUs | Disk GB | Memory MB | Server Profile Template             | Server Hardware Type | Enclosure Group Name    |
    +----+------+---------+-----------+-------------------------------------+----------------------+-------------------------+
    | 1  | 8    | 120     | 8192      | second-virt-server-profile-template | BL460c Gen9 1        | virtual-enclosure-group |
    +----+------+---------+-----------+-------------------------------------+----------------------+-------------------------+

After choosing a valid configuration ID, you'll be prompted to name the new
flavor. If you leave the field blank, a default name will be used.

To list all flavors in Nova, use the command::

    $ nova flavor-list

For more information about the created Nova flavor, use the command::

    $ nova flavor-show [FLAVOR_UUID]


References
==========
.. [1] Dynamic allocation spec - https://review.openstack.org/#/c/275726/
.. [2] Driver documentation - http://docs.openstack.org/developer/ironic/drivers/oneview.html
.. [3] HP OneView - http://www8.hp.com/us/en/business-solutions/converged-systems/oneview.html
.. [4] OpenStack RC - http://docs.openstack.org/user-guide/common/cli_set_environment_variables_using_openstack_rc.html

