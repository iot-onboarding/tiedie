# Copyright (c) 2023, Cisco and/or its affiliates.
# All rights reserved.
# See LICENSE file in this distribution.
# SPDX-License-Identifier: Apache-2.0

import uuid
from http import HTTPStatus
from flask import Response, jsonify
from ble_operations.operation import Operation


class Service:
    def __init__(self, uuid: str, service_handle: int):
        self.uuid = uuid
        self.service_handle = service_handle
        self.characteristics: dict[str, Characteristic] = {}


class Characteristic:
    def __init__(self, uuid: str, char_handle: int, properties: int):
        self.uuid = uuid
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
    def __init__(self, uuid: str, desc_handle: int):
        self.uuid = uuid
        self.desc_handle = desc_handle


class DiscoverOperation(Operation):
    def __init__(self, lib, handle: int, retries: int = 3, services=[]):
        super().__init__(lib)
        self.handle = handle
        self.requested_services = services
        self.retries = retries
        self.services: dict[str, Service] = {}

    def run(self):
        self.lib.bt.gatt.discover_primary_services(self.handle)  # type: ignore

        self.wait()

        retries = 0

        for _ in range(self.retries + 1):

            if self.result != 0:
                self.log.error(f"failed to discover services: {self.result}")
                continue

            for service in self.services.values():
                self.lib.bt.gatt.discover_characteristics(  # type: ignore
                    self.handle, service.service_handle)
                self.current_service = service

                self.wait()

                if self.result != 0:
                    self.log.error(
                        f"failed to discover characteristics: {self.result}")
                    continue

                for characteristic in service.characteristics.values():
                    self.current_characteristic = characteristic
                    self.lib.bt.gatt.discover_descriptors(  # type: ignore
                        self.handle, characteristic.char_handle)

                    self.wait()

                    if self.result != 0:
                        self.log.error(
                            f"failed to discover descriptors: {self.result}")
                        continue

            self.is_done = True
            break

        if retries == self.retries + 1:
            self.is_done = True

    def bt_evt_gatt_service(self, evt):
        if evt.connection == self.handle:
            uuid = evt.uuid[::-1].hex()

            self.services[uuid] = Service(uuid, evt.service)

    def bt_evt_gatt_characteristic(self, evt):
        if evt.connection == self.handle:
            uuid = evt.uuid[::-1].hex()

            self.current_service.characteristics[uuid] = Characteristic(
                uuid, evt.characteristic, evt.properties)

    def bt_evt_gatt_descriptor(self, evt):
        if evt.connection == self.handle:
            uuid = evt.uuid[::-1].hex()

            self.current_characteristic.descriptors[uuid] = Descriptor(
                uuid, evt.descriptor)

    def bt_evt_gatt_procedure_completed(self, evt):
        if evt.connection == self.handle:
            self.result = evt.result
            self.set()
            self.clear()

    def response(self) -> tuple[Response, int]:
        device_services = [
            {
                "serviceID": service.uuid,
                "characteristics": [
                    {
                        "characteristicID": characteristic.uuid,
                        "flags": characteristic.properties,
                        "descriptors": [
                            {
                                "descriptorID": descriptor.uuid,
                            } for descriptor in characteristic.descriptors.values()
                        ],
                    } for characteristic in service.characteristics.values()
                ],
            } for service in self.services.values() if self.requested_services is [] or service.uuid in self.requested_services
        ]

        return jsonify({
            "status": "SUCCESS",
            "id": "",
            "requestID": uuid.uuid4(),
            "services": device_services
        }), HTTPStatus.OK

    def __repr__(self):
        return f"DiscoverOperation({self.handle})"
