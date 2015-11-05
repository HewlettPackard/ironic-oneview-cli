ironic-oneview CLI
==================

Overview
--------

The ironic-oneview is a command line interface tool for easing the use
of OneView Driver for Ironic. It allows a OneView Driver user to create
Ironic nodes and Nova flavors which are compatible with Server Hardwares
in OneView in a simple way.

Installation
------------

To install the ironic-oneview CLI tool you can use the following
command:

::

    pip install ironic-oneview-cli

Running the CLI tool without passing a configuration file and if there
isn't any configuration file in the python default path, the tool will
ask the user for the credential which will be used to connect to Ironic,
Nova and OneView, after get this credentials the tool creates a default
configuration file in the default python path.

Configuration
-------------

You can generate a configuration file using the follow command:

::

    ironic-oneview genconfig

The tool will now prompt you to type each credential needed to run it.
In the end the tool prompt you to type the path where the config file
will be saved.

If you want to pass a configuration file you can execute the CLI tool
commands passing a --config-file or -c parameter as in the example
below:

::

    ironic-oneview --config-file <your configuration file> <command>

Node Creation
-------------

You can create nodes in Ironic based on OneView machines using the
following command:

::

    ironic-oneview node-create

The tool will now prompt you to choose a valid Server Profile Template
from the ones listed, which were retrieved from your OneView appliance.

::

    +----+------------------------+----------------------+---------------------------+
    | Id | Name                   | Enclosure Group Name | Server Hardware Type Name |
    +----+------------------------+----------------------+---------------------------+
    | 1  | template-dcs-virt-enc3 | virt-enclosure-group | BL460c Gen8 3             |
    | 2  | template-dcs-virt-enc4 | virt-enclosure-group | BL660c Gen9 1             |
    +----+------------------------+----------------------+---------------------------+  

After choosing a valid SPT, the tool lists the available Server Hardware
objects that match the chosen SPT, and prompt you to choose the ones you
want to be used to create Ironic nodes.

::

    Listing compatible Server Hardware objects..
    +----+-----------------+------+-----------+----------+----------------------+---------------------------+
    | Id | Name            | CPUs | Memory MB | Local GB | Enclosure Group Name | Server Hardware Type Name |
    +----+-----------------+------+-----------+----------+----------------------+---------------------------+
    | 1  | VIRT-enl, bay 5 | 8    | 32768     | 120      | virt-enclosure-group | BL460c Gen8 3             |
    | 2  | VIRT-enl, bay 8 | 8    | 32768     | 120      | virt-enclosure-group | BL460c Gen8 3             |
    +----+-----------------+------+-----------+----------+----------------------+---------------------------+

Note that you can choose many Server Hardware items in one go. In order
to do that, type the respective IDs separated by blank spaces. If you
choose more than one ID, the request will only be completed if all the
values are valid.

Once you type all the values, nodes are then created corresponding to
each respective Server Hardware and put in Enroll provision state.

Flavor Creation
---------------

You can create flavors using the following command:

::

    ironic-oneview flavor-create

You should now be able to see the possible flavors to be created and a
prompt asking for the id of the flavor you want to create. The next step
is to choose the name of the flavor which can either be customised or
the default suggested by ironic-oneview CLI.

Press Enter and, if everything goes well, your flavor will be shown when
running:

::

    nova flavor-list

-  Free software: Apache license
-  Source: http://git.lsd.ufcg.edu.br/ironicdrivers/ironic-oneview-tools
-  Bugs: TODO

Features
--------

-  TODO

