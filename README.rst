# Ironic-OneView-Tools

## Introduction

The Ironic-OneView-Tools is a CLI tool for easing the use of OneView Driver for Ironic. It
allows an OneView Driver user to create Ironic nodes and Nova flavors which are compatible
with Server Hardwares in OneView in a simple way. 

## Installation

To install the Ironic-OneView-Tools CLI tool you can use the following command: 

```
pip install ironic-oneview-cli
```

The CLI tool automatically creates a default conf file, *ironic-oneview.conf*, which should 
contains the credentials that enable the connection of CLI tool with Ironic, Nova and OneView.
The *ironic-oneview.conf* can be found in the directory: */etc/ironic-oneview/ironic-oneview.conf*

## Node Creation

If the credentials in *ironic-oneview.conf* are correct, you can create nodes using the 
following command:

```
ironic-oneview node-create
```

If you want to pass a different configuration file you can create nodes using one of
the following commands:

```
ironic-oneview --config-file <your configuration file> node-create
```

```
ironic-oneview -c <your configuration file> node-create
```

The tool will now prompt you to choose a valid Server Profile Template from the ones listed, 
which were retrieved from your OneView appliance.

```
+----+------------------------+----------------------+---------------------------+
| Id | Name                   | Enclosure Group Name | Server Hardware Type Name |
+----+------------------------+----------------------+---------------------------+
| 1  | template-dcs-virt-enc3 | virt-enclosure-group | BL460c Gen8 3             |
| 2  | template-dcs-virt-enc4 | virt-enclosure-group | BL660c Gen9 1             |
+----+------------------------+----------------------+---------------------------+  
```

After choosing a valid SPT, the tool lists the available Server Hardware objects that match the 
chosen SPT, and prompt you to choose the ones you want to be used to create Ironic nodes.

```
Listing compatible Server Hardware objects..
+----+-----------------+------+-----------+----------+----------------------+---------------------------+
| Id | Name            | CPUs | Memory MB | Local GB | Server Group Name    | Server Hardware Type Name |
+----+-----------------+------+-----------+----------+----------------------+---------------------------+
| 1  | VIRT-enl, bay 5 | 8    | 32768     | 120      | virt-enclosure-group | BL460c Gen8 3             |
| 2  | VIRT-enl, bay 8 | 8    | 32768     | 120      | virt-enclosure-group | BL460c Gen8 3             |
+----+-----------------+------+-----------+----------+----------------------+---------------------------+
```

Note that you can choose a set of Server Hardware objects in one go. In order to do that, type the respective 
IDs separated by blank spaces. If you choose more than one ID, the request will only be completed if all the 
values are valid.

Once you type all the values, nodes are then created corresponding to each respective Server Hardware and put 
in an enroll provision state.

## Flavor Creation

If the credentials in *ironic-oneview.conf* are correct, you can create flavors using the
following command:

```
ironic-oneview flavor-create
```

If you want to pass a different configuration file you can create flavors using one of
the following commands:

```
ironic-oneview --config-file <your configuration file> flavor-create
```

```
ironic-oneview -c <your configuration file> flavor-create
```

You should now be able to see the possible flavors to be created and a prompt asking for 
the id of the flavor you want to create. The next step is to choose the name of the flavor 
which can either be customised or the default suggested by ironic-oneview CLI.

Press Enter and, if everything goes well, your flavor will be shown when running:

```
nova flavor-list
```

[TODO - Description]

* Free software: Apache license
* Source: http://git.lsd.ufcg.edu.br/ironicdrivers/ironic-oneview-tools
* Bugs: TODO

Features
--------

* TODO
