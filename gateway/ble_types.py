# Copyright (c) 2023, Cisco Systems, Inc. and/or its affiliates.
# All rights reserved.
# See LICENSE file in this distribution.
# SPDX-License-Identifier: Apache-2.0
"""
BLE data classes for Service, Characteristic, Descriptor.
"""
import dataclasses

@dataclasses.dataclass
class Service:
    """
    This class represents a service in Bluetooth Low Energy (BLE)
    with a UUID and a service handle, containing characteristics as a
    dictionary.
    """
    service_id: str
    service_handle: int
    characteristics: dict[str, "Characteristic"] = dataclasses.field(
        default_factory=dict)


@dataclasses.dataclass
class Characteristic:
    """ Represents BLE characteristic with UUID, handle, and properties info. """

    def __init__(self, characteristic_id: str, char_handle: int, properties: int):
        self.characteristic_id = characteristic_id
        self.char_handle = char_handle

        self.properties: list[str] = []
        self.descriptors: dict[str, Descriptor] = {}

        if (properties & 0x02) == 0x02:
            self.properties.append("read")
        if (properties & 0x04) == 0x04:
            self.properties.append("write_no_response")
        if (properties & 0x08) == 0x08:
            self.properties.append("write")
        if (properties & 0x10) == 0x10:
            self.properties.append("notify")
        if (properties & 0x20) == 0x20:
            self.properties.append("indicate")
        if (properties & 0x80) == 0x80:
            self.properties.append("extended_props")
        if (properties & 0x101) == 0x101:
            self.properties.append("reliable_write")


@dataclasses.dataclass
class Descriptor:
    """ Class for BLE descriptor with UUID and handle attributes. """
    descriptor_id: str
    desc_handle: int
