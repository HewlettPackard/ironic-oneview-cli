==================
Ironic-OneView CLI
==================

Overview
========

The ironic-oneview is a ``command line interface tool`` for easing the use
of the OneView Driver for Ironic. It allows a user to easily create Ironic
nodes compatible with OneView ``Server Hardware`` objects as well as properly
configuring them. It also creates Nova flavors to match available Ironic
nodes representing a ``Server Hardware``.

For more information on *OneView* entities, see [1]_.

Installation
============

To install the ironic-oneview CLI tool, use the following command::

    pip install ironic-oneview-cli

Configuring the tool
====================

The ironic-oneview CLI tool uses a configuration file to get Ironic, Nova and
OneView credentials and addresses. To generate and configure such file
accordingly, run::

    ironic-oneview genconfig

This tool asks you for such information and creates a *~/ironic-oneview-cli.conf*
configuration file located at your home directory by default, or other
location of your choice.

If you prefer to create your own configuration file, it should look like this::

    [ironic]
    admin_user=<your admin user name>
    admin_password=<your admin password>
    admin_tenant_name=<your admin tenant name>
    auth_url=<your Ironic authentication url>
    insecure=<true,false>
    default_deploy_kernel_id=<your deploy kernel uuid>
    default_deploy_ramdisk_id=<your deploy ramdisk uuid>
    default_driver=<iscsi_pxe_oneview,agent_pxe_oneview>

    [nova]
    auth_url=<your Nova authentication url>
    username=<your admin username>
    password=<your admin password>
    tenant_name=<your tenant name>
    insecure=<true,false>

    [oneview]
    manager_url=<your OneView appliance url>
    username=<your OneView username>
    password=<your OneView password>
    allow_insecure_connections=<true,false>
    tls_cacert_file=<path to your CA certfile, if any>

Usage
=====

If your *~/ironic-oneview-cli.conf* configuration file is in your home directory, 
the tool will automatically use this conf. In this case, to run
ironic-oneview-cli, do::

    ironic-oneview <command>

If you chose to place this file in a different location, you should pass it
when starting the tool::

    ironic-oneview --config-file <path to your configuration file> <command>

or::

    ironic-oneview -c <path to your configuration file> <command>

Note that, in order to run this tool, you only have to pass the configuration
file previously created containing the required credentials and addresses.

Features
========

Node Creation
^^^^^^^^^^^^^

To create nodes in Ironic based on *OneView* available ``Server Hardware``
objects, use the following command::

    ironic-oneview node-create

The tool will now prompt you to choose a valid ``Server Profile Template``
(SPT) from the available ones listed, which were retrieved from your *OneView*
appliance.::

    Retrieving Server Profile Templates from OneView...
    +----+------------------------+----------------------+---------------------------+
    | Id | Name                   | Enclosure Group Name | Server Hardware Type Name |
    +----+------------------------+----------------------+---------------------------+
    | 1  | template-dcs-virt-enc3 | virt-enclosure-group | BL460c Gen8 3             |
    | 2  | template-dcs-virt-enc4 | virt-enclosure-group | BL660c Gen9 1             |
    +----+------------------------+----------------------+---------------------------+  

After choosing a valid ``SPT``, the tool lists the available Server Hardware
objects that match the chosen ``SPT``, and prompt you to choose the ones you
want to use to create Ironic nodes.::

    Listing compatible Server Hardware objects...
    +----+-----------------+------+-----------+----------+----------------------+---------------------------+
    | Id | Name            | CPUs | Memory MB | Local GB | Enclosure Group Name | Server Hardware Type Name |
    +----+-----------------+------+-----------+----------+----------------------+---------------------------+
    | 1  | VIRT-enl, bay 5 | 8    | 32768     | 120      | virt-enclosure-group | BL460c Gen8 3             |
    | 2  | VIRT-enl, bay 8 | 8    | 32768     | 120      | virt-enclosure-group | BL460c Gen8 3             |
    +----+-----------------+------+-----------+----------+----------------------+---------------------------+

Note that you can choose many ``Server Hardware`` objects in one go. In order
to do that, type the respective IDs separated by blank spaces. If you
choose more than one ID, the request will only be completed if all the
values are valid.

Once you've typed all the values, nodes corresponding to each respective
``Server Hardware`` are then created and put in an *enroll* provision state.
If everything goes well, your nodes will be shown when running::

    ironic node-list

Flavor Creation
^^^^^^^^^^^^^^^

To create flavors compatible with available Ironic *OneView* nodes, use the
following command::

    ironic-oneview flavor-create

The tool will now prompt you to choose a valid flavor configuration, according
to the config of available nodes.::

    +----+------+---------+-----------+
    | Id | CPUs | Disk GB | Memory MB |
    +----+------+---------+-----------+
    | 1  | 32   | 120     | 16384     |
    +----+------+---------+-----------+

After choosing a valid configuration ID, you'll be prompted to name your
flavor. If you leave the field blank, a default name will be given. Press
Enter and, if everything goes well, your flavor is created and will be shown
when running::

    nova flavor-list

References
==========
.. [1] HP OneView - http://www8.hp.com/us/en/business-solutions/converged-systems/oneview.html

