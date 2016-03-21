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

The ironic-oneview CLI tool uses environment variables to get Ironic, Nova and
OneView credentials and addresses. The credentials for OpenStack must be loaded
from the ``PROJECT-openrc.sh`` provided by Horizon (The OpenStack Dashboard
Project) from your cloud controller. To download the ``PROJECT-openrc.sh`` from
Horizon, you must log in to the Horizon and go to Compute menu, access
Access & Security sub-menu, access the API Access tab, and donwload the
file by pressing the Download OpenStack RC File button.

To load the environment variables from ``PROJECT-openrc.sh`` accordingly, run::

    source PROJECT-openrc.sh

Then you will be asked to provide your OpenStack password and your OpenStack
credentials will be loaded.

For the HP OneView credentials you may use the command 'genrc' to generate and
configure the ironic-oneviewrc.sh file accordingly, run::

    ironic-oneview genrc

Then you will be asked to provide your HP OneView URL, username, and the uuid
from the Glance images for kernel and ramdisk, and the Ironic driver you going
to use. After insert these informations the ``ironic-oneviewrc.sh`` will be
generated.

To load the environment variables from ``ironic-oneviewrc.sh`` accordingly, run::

    source ironic-oneviewrc.sh

Then you will be asked to provide your HP OneView password and your HP OneView
credentials will be loaded.

Usage
=====

Once the necessary environment variables were set you are able to run the
ironic-oneview CLI tool by doing::

    ironic-oneview <command>

In the current version the possible commands are:

+--------------+--------------------------------------------------------------------+
| node-create  | Creates nodes in Ironic given a list of availableOneView servers.  |
+--------------+--------------------------------------------------------------------+
| flavor-create| Creates flavors based on OneView available Ironic nodes.           |
+--------------+--------------------------------------------------------------------+
|    genrc     | Generates the ironic-oneviewrc file according to user input.       |
+--------------+--------------------------------------------------------------------+
|    help      | Displays help about this program or one of its subcommands.        |
+--------------+--------------------------------------------------------------------+

For insecure connections the optional argument ``--insecure`` needs to be used.


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

After choosing a valid ``Server Profile Template``, the tool lists the
available Server Hardware objects that match the chosen ``Server Profile
Template``, and prompt you to choose the ones you
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

    +----+------+---------+-----------+-------------------------------------+----------------------+-------------------------+
    | Id | CPUs | Disk GB | Memory MB | Server Profile Template             | Server Hardware Type | Enclosure Group Name    |
    +----+------+---------+-----------+-------------------------------------+----------------------+-------------------------+
    | 1  | 8    | 120     | 8192      | second-virt-server-profile-template | BL460c Gen9 1        | virtual-enclosure-group |
    +----+------+---------+-----------+-------------------------------------+----------------------+-------------------------+

After choosing a valid configuration ID, you'll be prompted to name your
flavor. If you leave the field blank, a default name will be given. Press
Enter and, if everything goes well, your flavor is created and will be shown
when running::

    nova flavor-list

References
==========
.. [1] HP OneView - http://www8.hp.com/us/en/business-solutions/converged-systems/oneview.html