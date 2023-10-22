# Welcome to TieDie IoT

This package enables IoT device provisioning and communication for
non-IP devices (e.g., BLE, Zigbee) via an application layer gateway.
Want to deploy a new application?  You no longer need to lay down
additional bridges or make use of USB dongles.

## How do I use it?

Two SDKs are provided, Java and Python.  A gateway then can operate
on a Linux system with an 802.15.4 interface.  The order of operations
is this:

1. Provision applications to control devices
2. Provision devices
3. Connect to devices
4. Send and receive requests to and from devices.  This includes
   setting up indications and notifications.
5. Register applications and subscribe to MQTT topics that return
   the indications and notifications.
6. Disconnect when finished


## How do I contribute?

All are welcome, under the condition that no intellectual property
limitations are introduced.  The LICENSE in this distribution
applies.

## Standards

This repository contains code that implements-

 - draft-ietf-scim-device-model
 - draft-brinckman-asdf-nipc

With this combination, applications can control their non-IP devices
using the SCIM provisioning interface and an application layer gateway
(ALG).  The specifications support provisioning of IP devices as well.
The code will support those functions in the future.

Please see the LICENSE file for licensing.

## Organization

The 'gateway' directory contains code that will run in a container or
natively to communicate currently with BLE devices.

The 'python-sdk' and 'java-sdk' directories contain code necessary to
interface an application to the gateway.

Got an Issue?  Your contributions are welcome.
