# Copyright (c) 2023, Cisco Systems, Inc. and/or its affiliates.
# All rights reserved.
# See LICENSE file in this distribution.
# SPDX-License-Identifier: Apache-2.0

"""

Classes for modeling BLE services, characteristics, and descriptors,
along with an operation for discovering these attributes in BLE devices.

"""

from silabs.ble_operations.operation import Operation
from ble_types import Service, Characteristic, Descriptor
from access_point_responses import DiscoverResponse


class DiscoverOperation(Operation):
    """ This class discovers BLE services, characteristics, and descriptors using callbacks. """

    current_service: Service
    current_characteristic: Characteristic
    result: int

    def __init__(self, lib, handle: int, retries: int = 3, services: list[dict[str, str]] = None):
        super().__init__(lib)
        self.handle = handle
        self.requested_services = services
        self.retries = retries
        self.services: dict[str, Service] = {}

    def run(self):
        """ run function """
        self.lib.bt.gatt.discover_primary_services(self.handle)  # type: ignore

        self.wait()

        if self.result != 0:
            self.log.error("failed to discover services: %d", self.result)
            return

        for service in self.services.values():
            self.lib.bt.gatt.discover_characteristics(  # type: ignore
                self.handle, service.service_handle)
            self.current_service = service

            self.wait()

            if self.result != 0:
                self.log.error(
                    "failed to discover characteristics: %d", self.result)
                return

            for characteristic in service.characteristics.values():
                self.current_characteristic = characteristic
                self.lib.bt.gatt.discover_descriptors(  # type: ignore
                    self.handle, characteristic.char_handle)

                self.wait()

                if self.result != 0:
                    self.log.error(
                        "failed to discover descriptors: %d", self.result)
                    return

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

    def response(self):
        """ Returns a DiscoverResponse with the discovered services. """
        # Only include requested services if specified
        if self.requested_services:
            services = [s for s in self.services.values() if s.service_id in self.requested_services]
        else:
            services = list(self.services.values())
        return DiscoverResponse(address=str(self.handle), services=services)

    def __repr__(self):
        return f"DiscoverOperation({self.handle})"
