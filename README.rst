==================
Ironic-OneView CLI
==================

Overview
========

The ``Ironic-OneView CLI`` is a command line interface tool for easing the
use of the OneView Driver for Ironic. It allows an user to easily create Ironic
nodes compatible with OneView Server Hardware objects, as well as properly
configuring them. It also creates Nova flavors to match available Ironic nodes
representing a ``Server Hardware``.

For more information on *HP OneView* entities, see [1]_.


Installation
============

To install the ironic-oneview CLI, use the following command::

    $ pip install ironic-oneview-cli


Usage
=====

Once the command line parameters or the necessaries environment variables are
set, the ``Ironic-OneView CLI`` is ready to be used.

Synopsis::

    $ ironic-oneview <subcommand>


In the current version of ``Ironic-OneView CLI`` the available subcommands are:

+---------------+-----------------------------------------------------------------+
|  node-create  | Creates nodes based on available HP OneView Server Hardware.    |
+---------------+-----------------------------------------------------------------+
| flavor-create | Creates flavors based on available Ironic nodes.                |
+---------------+-----------------------------------------------------------------+
|     genrc     | Generates the ironic-oneviewrc.sh file according to user input. |
+---------------+-----------------------------------------------------------------+
|     help      | Displays help about this program or one of its subcommands.     |
+---------------+-----------------------------------------------------------------+


Configuration
=============

For use the ``Ironic-Oneview CLI`` you must download the OpenStack RC file
from your OpenStack cloud controller. Once you have the OpenStack RC and the
credentials loaded as environment variables, you must run the ``genrc``
subcommand to generate the ``ironic-oneviewrc.sh`` file::

    $ ironic-oneview genrc

Since you have the ``ironic-oneviewrc.sh`` file, load the environment
variables, by doing::

    $ source ironic-oneviewrc.sh

For more information how to download and load the *OpenStack RC*, see [2]_.


Features
========

Node creation
^^^^^^^^^^^^^

To create Ironic nodes based on available HP OneView Server Hardware objects,
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

The tool will ask you to choose a ``Server Hardware`` to be used as base to the
Ironic node you are creating.::

    Listing compatible Server Hardware objects...
    +----+-----------------+------+-----------+----------+----------------------+---------------------------+
    | Id | Name            | CPUs | Memory MB | Local GB | Enclosure Group Name | Server Hardware Type Name |
    +----+-----------------+------+-----------+----------+----------------------+---------------------------+
    | 1  | VIRT-enl, bay 5 | 8    | 32768     | 120      | virt-enclosure-group | BL460c Gen8 3             |
    | 2  | VIRT-enl, bay 8 | 8    | 32768     | 120      | virt-enclosure-group | BL460c Gen8 3             |
    +----+-----------------+------+-----------+----------+----------------------+---------------------------+

Note that you can create multiple Ironic nodes at the same time. For this, you
can type multiples ``Server Hardware`` IDs separated by blank spaces. The
created Ironic nodes will have *enroll* provisioning state.

For list all nodes in Ironic, use the command::

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

After choosing a valid configuration ID, you'll be prompted to name your
flavor. If you leave the field blank, a default name will be given.

For list all flavors in Nova, use the command::

    $ nova flavor-list

For more information about the created Nova flavor, use the command::

    $ nova flavor-show [FLAVOR_UUID]


References
==========
.. [1] HP OneView - https://www.hpe.com/us/en/integrated-systems/software.html
.. [2] OpenStack RC - http://docs.openstack.org/user-guide/common/cli_set_environment_variables_using_openstack_rc.html
