==================
Ironic-OneView CLI
==================

Overview
========

Ironic-OneView CLI is a command line interface tool for easing the use of the
OneView Drivers for Ironic. It allows the user to easily manage:

- Ironic nodes compatible with OneView Server Hardware objects;
- Nova flavors matching available Ironic nodes that use OneView drivers;
- Ironic ports mapping Server Hardware ports.

.. note::
   This tool works with OpenStack Identity API v2.0 and v3.

.. note::
   This tool works with OpenStack Ironic API microversion '1.31'.

----

For more information on *HPE OneView* entities, see
`here <https://www.hpe.com/us/en/integrated-systems/software.html>`_.

Installation
============

To install Ironic-OneView CLI from PyPI, use the following command::

    $ pip install ironic-oneview-cli

.. note::
   Ocata/Newton users, we recommend using version 0.6.0

Configuration
=============

Ironic-Oneview CLI uses credentials loaded into environment variables by
the *OpenStack RC* file (downloaded from OpenStack Horizon), and the Ironic
OneView CLI RC file, which sample file can be generated using the following
``genrc`` subcommand::

    $ ironic-oneview genrc > ironic-oneviewrc.sh

Once the ``ironic-oneviewrc.sh`` is populated with OneView credentials using
any text editor, it can be loaded by running the following::

    $ source ironic-oneviewrc.sh

Credentials can be passed alternatively as command line parameters. A help
message informing of which parameters should be used is shown by running
the command the following::

    $ ironic-oneview help

For more information how to obtain and load the *OpenStack RC* file, see
`here <http://docs.openstack.org/user-guide/common/cli_set_environment_variables_using_openstack_rc.html>`_.


Usage
=====

Once the necessary environment variables and command line parameters are set,
Ironic OneView CLI is ready to be used. The current version of Ironic-OneView
CLI provides the following interactive subcommands:

+--------------------+---------------------------------------------------------------------+
|     node-create    | Creates Ironic nodes based on available HPE OneView Server Hardware.|
+--------------------+---------------------------------------------------------------------+
|    flavor-create   | Creates Nova flavors based on available Ironic nodes.               |
+--------------------+---------------------------------------------------------------------+
|     port-create    | Creates a new Ironic Port based on available Ironic nodes.          |
+--------------------+---------------------------------------------------------------------+
|     node-delete    | Deletes multiple Ironic nodes.                                      |
+--------------------+---------------------------------------------------------------------+
|        genrc       | Generates a sample Ironic-OneView CLI RC file.                      |
+--------------------+---------------------------------------------------------------------+
|        help        | Displays help about this program or one of its subcommands.         |
+--------------------+---------------------------------------------------------------------+

Any ironic-oneview-cli subcommand can be run in debugging mode with the --debug
parameter, as in the following command::

    $ ironic-oneview --debug node-create


Features
========

Node creation
^^^^^^^^^^^^^

To create Ironic nodes based on available HPE OneView ``Server Hardware``
objects, use the following command::

    $ ironic-oneview node-create

The tool retrieves all server profile templates previously created in OneView.
It builds a list with the Name, Enclosure Group Name and Server Hardware Type
Name (as shown in the table), and assigns an id that should be used by the
administrator to select which ``Server Profile Template`` should be used for node
creation::

    +----+------------------------+----------------------+---------------------------+
    | Id | Name                   | Enclosure Group Name | Server Hardware Type Name |
    +----+------------------------+----------------------+---------------------------+
    | 1  | template-dcs-virt-enc3 | virt-enclosure-group | BL460c Gen8 3             |
    | 2  | template-dcs-virt-enc4 | virt-enclosure-group | BL660c Gen9 1             |
    +----+------------------------+----------------------+---------------------------+

Once the user has chosen a valid ``Server Profile Template``, the tool lists the
available ``Server Hardware`` matching it as shown in the following table::

    +----+-----------------+------+-----------+----------+----------------------+---------------------------+
    | Id | Name            | CPUs | Memory MB | Local GB | Enclosure Group Name | Server Hardware Type Name |
    +----+-----------------+------+-----------+----------+----------------------+---------------------------+
    | 1  | VIRT-enl, bay 5 | 8    | 32768     | 120      | virt-enclosure-group | BL460c Gen8 3             |
    | 2  | VIRT-enl, bay 8 | 8    | 32768     | 120      | virt-enclosure-group | BL460c Gen8 3             |
    +----+-----------------+------+-----------+----------+----------------------+---------------------------+

Notice that multiple Ironic nodes can be created at once. That can be achieved,
by selecting multiple ``Server Hardware`` IDs separated by blank spaces. The
created Ironic nodes will be in the *enroll* provisioning state.

This command also creates an Ironic port to be used by the node, the port is
created in the same way as the port-create command (see below) with the
parameter ``--mac`` also optional.


.. note::
   If *os_inspection_enabled = True*, the created node will not have the hardware
   properties (*cpus*, *memory_mb*, *local_gb*, *cpu_arch*) set in the node properties.
   This will be discovered during the Ironic Hardware Inspection.

----

Alternatively, the ``Server Profile Template`` can be specified using the
parameter ``--server-profile-template`` so that the tool prompts the list of
``Server Hardware`` to be used, as shown in the following command::

    $ ironic-oneview node-create [--server-profile-template-name | -spt <spt_name>]

A collection of nodes sharing the same ``Server Profile Template`` can be set up
in a batch by using the following command::

    $ ironic-oneview node-create [--number | -n <number>]

.. note::
   You can use both arguments at once.

In order to enable *Networking OneView ML2 Driver*, the following command to
create a node with this information set to its driver_info field::

    $ ironic-oneview node-create --use-oneview-ml2-driver

For more information on *Networking OneView ML2 Driver*, see
`here <https://github.com/HewlettPackard/ironic-driver-oneview/tree/master/networking-oneview>`_.

With the Driver composition reform, the default behavior is to create a node
using a hardware type. With this feature, specific hardware type compatible
interfaces can be dynamically set to the node, such as: ``OpenStack Power
Interface``, ``OpenStack Management Interface``, ``OpenStack Inspect
Interface``, ``OpenStack Deploy Interface``.
Use the following command to create a node with this hardware type and
interfaces::

    $ ironic-oneview node-create --os-driver <hardware_type> --os-power-interface <power_interface>
      --os-management-interface <management_interface> --os-inspect-interface <inspect_interface>
      --os-deploy-interface <deploy_interface>

If you want to create the node using the classic driver, use the following
command::

    $ ironic-oneview node-create --classic

For more information on the *Driver composition reform*, see
`here <https://specs.openstack.org/openstack/ironic-specs/specs/approved/driver-composition-reform.html>`_.

----

To list all nodes in Ironic, use the following command::

    $ openstack baremetal node list

For more information about the created Ironic node, use the following command::

    $ openstack baremetal node show <node>


Flavor creation
^^^^^^^^^^^^^^^

In order to launch bare metal instances, the user needs to specify a flavor
compatible with an available Ironic Node, which maps directly to an available
``Server Hardware``. The following interactive command can be used to create Nova
flavors::

    $ ironic-oneview flavor-create

The tool will prompt with a list of possible new flavors, according to the
configuration of enrolled Ironic nodes::

    +----+------+---------+-----------+-------------------------------------+----------------------+-------------------------+
    | Id | CPUs | Disk GB | Memory MB | Server Profile Template             | Server Hardware Type | Enclosure Group Name    |
    +----+------+---------+-----------+-------------------------------------+----------------------+-------------------------+
    | 1  | 8    | 120     | 8192      | second-virt-server-profile-template | BL460c Gen9 1        | virtual-enclosure-group |
    +----+------+---------+-----------+-------------------------------------+----------------------+-------------------------+

After choosing a valid configuration, the user can optionally specify a name for
the new flavor. If left blank, a default name will be used. Additional
information from Server Hardware Type, Enclosure Group and Server Profile
Template is automatically added by default to the flavor metadata. Use Horizon
to delete the Enclosure Group info, for example, so that a flavor matches Server
Hardware in all available enclosures.

----

To list all flavors in Nova, use the command::

    $ openstack flavor list

For more information about the created Nova flavor, use the command::

    $ openstack flavor show <flavor>


Port creation
^^^^^^^^^^^^^

Creates a port for an existing Ironic node. The following interactive command
can be used to create Ironic ports::

    $ ironic-oneview port-create [--mac | -m <mac>] <node>

In the case when the user does not specify a port, the result will be an Ironic
port for the first ``-a`` available port at the ``Server Hardware`` used by
ironic-node.

To list all ports in Ironic, use the command::

    $ openstack baremetal port list

For more information about the created Ironic port, use the following command::

    $ openstack baremetal port show <port>


Node delete
^^^^^^^^^^^

The tool also offers the option to delete a specific number of Ironic nodes. For
that use the following command::

    $ ironic-oneview node-delete --number <number>

To delete all Ironic nodes, use the following command::

    $ ironic-oneview node-delete --all


Contributing
^^^^^^^^^^^^

Fork it, branch it, change it, commit it, and pull-request it. We are passionate
about improving this project, and are glad to accept help to make it better.
However, keep the following in mind: We reserve the right to reject changes that
we feel do not fit the scope of this project. For feature additions, please open
an issue to discuss your ideas before doing the work.


Feature Requests
^^^^^^^^^^^^^^^^

If you have a need not being met by the current implementation, please let us
know (via a new issue). This feedback is crucial for us to deliver a useful
product. Do not assume that we have already thought of everything, because we
assure you that is not the case.


Testing
^^^^^^^

We have already packaged everything you need to do to verify if the code is
passing the tests. The tox script wraps the unit tests execution against Python
2.7, 3.5 and pep8 validations.
Run the following command::

    $ tox
