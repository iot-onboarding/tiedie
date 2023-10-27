# Copyright (c) 2023, Cisco and/or its affiliates.
# All rights reserved.
# See LICENSE file in this distribution.
# SPDX-License-Identifier: Apache-2.0

"""

Classes for modeling BLE services, characteristics, and descriptors,
along with an operation for discovering these attributes in BLE devices.

"""

import uuid
from http import HTTPStatus
from flask import Response, jsonify
from silabs.ble_operations.operation import Operation


class Service:
    """
    This class represents a service in Bluetooth Low Energy (BLE) 
    with a UUID and a service handle, containing characteristics as a
    dictionary.
    """

    def __init__(self, service_id: str, service_handle: int):
        self.uuid = service_id
        self.service_handle = service_handle
        self.characteristics: dict[str, Characteristic] = {}


class Characteristic:
    """ Represents BLE characteristic with UUID, handle, and properties info. """

    def __init__(self, characteristic_id: str, char_handle: int, properties: int):
        self.uuid = characteristic_id
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


class Descriptor:
    """ Class for BLE descriptor with UUID and handle attributes. """

    def __init__(self, descriptor_id: str, desc_handle: int):
        self.uuid = descriptor_id
        self.desc_handle = desc_handle


class DiscoverOperation(Operation):
    """ This class discovers BLE services, characteristics, and descriptors using callbacks. """

    current_service: Service
    current_characteristic: Characteristic
    result: int

    def __init__(self, lib, handle: int, retries: int = 3, services=None):
        super().__init__(lib)
        self.handle = handle
        self.requested_services = services
        self.retries = retries
        self.services: dict[str, Service] = {}

    def run(self):
        """ run function """
        self.lib.bt.gatt.discover_primary_services(self.handle)  # type: ignore

        self.wait()

        retries = 0

        for _ in range(self.retries + 1):

            if self.result != 0:
                self.log.error("failed to discover services: %d", self.result)
                continue

            for service in self.services.values():
                self.lib.bt.gatt.discover_characteristics(  # type: ignore
                    self.handle, service.service_handle)
                self.current_service = service

                self.wait()

                if self.result != 0:
                    self.log.error(
                        "failed to discover characteristics: %d", self.result)
                    continue

                for characteristic in service.characteristics.values():
                    self.current_characteristic = characteristic
                    self.lib.bt.gatt.discover_descriptors(  # type: ignore
                        self.handle, characteristic.char_handle)

                    self.wait()

                    if self.result != 0:
                        self.log.error(
                            "failed to discover descriptors: %d", self.result)
                        continue

            self.is_done = True

        if retries == self.retries + 1:
            self.is_done = True

    def bt_evt_gatt_service(self, evt):
        """ Processes Bluetooth GATT service discovery event, stores discovered services. """
        if evt.connection == self.handle:
            service_id = evt.uuid[::-1].hex()

            self.services[service_id] = Service(service_id, evt.service)

    def bt_evt_gatt_characteristic(self, evt):
        """ Handles Bluetooth GATT characteristic discovery, storing UUID and properties. """
        if evt.connection == self.handle:
            characteristic_id = evt.uuid[::-1].hex()

            self.current_service.characteristics[characteristic_id] = Characteristic(
                characteristic_id, evt.characteristic, evt.properties)

    def bt_evt_gatt_descriptor(self, evt):
        """ Handles Bluetooth GATT descriptor discovery, storing UUID and descriptor handle. """
        if evt.connection == self.handle:
            descriptor_id = evt.uuid[::-1].hex()

            self.current_characteristic.descriptors[descriptor_id] = Descriptor(
                descriptor_id, evt.descriptor)

    def bt_evt_gatt_procedure_completed(self, evt):
        """ bt_evt_gatt_procedure_completed function """
        if evt.connection == self.handle:
            self.result = evt.result
            self.set()
            self.clear()

    def response(self) -> tuple[Response, int]:
        """ response function """
        return jsonify({
            "status": "SUCCESS",
            "requestID": uuid.uuid4(),
            "services": [
                {
                    "uuid": service.uuid,
                    "characteristics": [
                        {
                            "serviceID": characteristic.uuid,
                            "flags": characteristic.properties,
                            "descriptors": [
                                {
                                    "characteristicID": descriptor.uuid,
                                } for descriptor in characteristic.descriptors.values()
                            ],
                        } for characteristic in service.characteristics.values()
                    ],
                } for service in self.services.values()
                if self.requested_services is None or
                service.uuid in self.requested_services
            ]
        }), HTTPStatus.OK

    def __repr__(self):
        return f"DiscoverOperation({self.handle})"
