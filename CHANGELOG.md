# 1.2.1

#### Bugfixes & Enhancements
- Sort output of ironic-oneview-cli commands for SH and SPT
- Fix certificate environment variable name on genrc

# 1.2.0

#### Notes
- Update python-ilorest-library version to 2.1.0

#### Bugfixes & Enhancements
- Update default driver and inspector values on genrc
- Update README
- Enabled tests and coverage evaluation by Travis CI

#### New features
- Add port-create command
- Create port automatically when creating a node

# 1.1.0

#### Notes
- Remove python-oneviewclient dependency
- Add python-hpOneView dependency

#### Bugfixes & Enhancements
- Shows node UUID in node creation message

#### New features
- Introduce driver composition to ironic-oneview-cli
- Create nodes with classic drivers using --classic


# 1.0.0

#### Notes
- Deprecate pre-allocation mode


# 0.6.0

#### Notes
- Update minimal version of Ironic API to 1.22

#### Bugfixes & Enhancements
- Fix node and flavor creation using DL servers

#### New features
- Enable HP OneView Mechanism Driver for Neutron ML2 plugin during node creation


# 0.5.1

#### Bugfixes & Enhancements
- Fix flavor-create command to work with DL servers


# 0.5.0

#### Bugfixes & Enhancements
- Add column when listing server hardware showing if node is already enrolled in Ironic
- Updates 'genrc' command for create a base config file instead of ask user each value
- Updates tool documentation

#### New features
- Introduces node creation missing hardware properties in case of hardware inspection


# 0.4.1

#### Bugfixes & Enhancements
- Fix --insecure parameter when creating a flavor


# 0.4.0

#### Bugfixes & Enhancements
- Using Keystone v3


# 0.3.0

#### New features
- Add commands for migration of nodes to dynamic_allocation
- Enroll nodes with fake_oneview driver

# 0.2.0

#### Notes
- Using python-oneviewclient with ClientV2


# 0.1.1

#### Notes
-Setting basic test environment


# 0.1.0

#### Bugfixes & Enhancements
- Removed ironic-oneview-cli.conf and genconfig command

#### New features
- Uses envvars/parameters from openrc/oneviewrc files to login
- Added genrc command to generate oneviewrc file
- Creates nodes with dynamic_allocation flag


# 0.0.2

#### Bugfixes & Enhancements
- Fix string reception on genconfig
- Changes on flavor creation


# 0.0.1

#### Notes
- Pre-beta version

