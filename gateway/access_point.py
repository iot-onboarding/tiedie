# Copyright (c) 2023, Cisco and/or its affiliates.
# All rights reserved.
# See LICENSE file in this distribution.
# SPDX-License-Identifier: Apache-2.0

"""

This script defines BLE communication. Manages device connections,
actions like scanning, reading/writing, and subscribing/unsubscribing
to characteristics.

"""

import uuid
import threading
from http import HTTPStatus

from flask import Response, jsonify

from ble_operations.connect import ConnectOperation
from ble_operations.disconnect import DisconnectOperation
from ble_operations.discover import DiscoverOperation, Service
from ble_operations.operation import Operation
from ble_operations.read import ReadOperation
from ble_operations.scan import ScanOperation
from ble_operations.subscribe import SubscribeOperation
from ble_operations.write import WriteOperation
from config import SL_BT_CONFIG_MAX_CONNECTIONS
from data_producer import DataProducer
from silabs.common.util import BluetoothApp, get_connector


class ConnectionRequest:
    """ class containing attributes for a connection request """
    def __init__(self, address: str, handle: int, services: dict[str, Service]):
        self.address = address
        self.handle = handle
        self.services = services


class AccessPoint(BluetoothApp):
    """ Manages Bluetooth Low Energy (BLE) operations and connections."""
    operations: list[Operation] = []

    # map of addresses to connection handles
    conn_reqs: dict[str, ConnectionRequest] = {}

    def __init__(self, connector, data_producer: DataProducer):
        super().__init__(connector)
        self.ready = threading.Event()
        self.data_producer = data_producer

    def start(self):
        """ Start accesspoint function """
        super().start()

    def connectable(self):
        """ Check if new connections can be established """
        return len(self.conn_reqs) < SL_BT_CONFIG_MAX_CONNECTIONS

    def start_scan(self):
        """ Start scanning for devices """
        scan_operation = ScanOperation(self.lib, self.data_producer)
        self.operations.append(scan_operation)

        scan_operation.run()

    def connect(self, address, services, retries=3) -> tuple[Response, int]:
        """ Connect to a device """
        if not self.connectable():
            reqstr = {"status": "FAILURE", "requestID": uuid.uuid4(), "reason": "max connections"}
            jsonstring = jsonify(reqstr)
            return jsonstring, HTTPStatus.BAD_REQUEST

        if address in self.conn_reqs:
            reqstr = {"status": "FAILURE", "requestID": uuid.uuid4(), "reason": "already connected"}
            jsonstring = jsonify(reqstr)
            return jsonstring, HTTPStatus.BAD_REQUEST

        operation = ConnectOperation(self.lib, self.data_producer, address, services, retries)
        self.operations.append(operation)

        operation.run()

        if not operation.is_set():
            return operation.response()

        discover_operation = DiscoverOperation(self.lib, operation.handle, services)
        self.operations.append(discover_operation)

        discover_operation.run()

        self.conn_reqs[address] = ConnectionRequest(
            address, operation.handle, discover_operation.services)

        return discover_operation.response()

    def discover(self, address, retries) -> tuple[Response, int]:
        """ Discover services of a device """
        if address not in self.conn_reqs:
            return jsonify({"status": "FAILURE", "reason": "not connected"}), HTTPStatus.BAD_REQUEST

        discover_operation = DiscoverOperation(
            self.lib, self.conn_reqs[address].handle, retries)
        self.operations.append(discover_operation)

        discover_operation.run()

        self.conn_reqs[address].services = discover_operation.services

        return discover_operation.response()

    def read(self, address: str, service_uuid: str, char_uuid: str) -> tuple[Response, int]:
        """ Read a characteristic of a device """
        if address not in self.conn_reqs:
            return jsonify({"status": "FAILURE", "reason": "not connected"}), HTTPStatus.BAD_REQUEST

        conn_req = self.conn_reqs[address]
        handle = conn_req.handle

        service = conn_req.services[service_uuid]
        characteristic = service.characteristics[char_uuid]

        operation = ReadOperation(self.lib, handle, characteristic.char_handle)
        self.operations.append(operation)
        operation.run()

        return operation.response()

    def write(self, address:str, service_uuid:str, char_uuid:str, value:str) -> tuple[Response,int]:
        """ Read a characteristic of a device """
        if address not in self.conn_reqs:
            return jsonify({"status": "FAILURE", "reason": "not connected"}), HTTPStatus.BAD_REQUEST

        conn_req = self.conn_reqs[address]
        handle = conn_req.handle

        service = conn_req.services[service_uuid]
        characteristic = service.characteristics[char_uuid]

        operation = WriteOperation(
            self.lib, handle, characteristic.char_handle, value)
        self.operations.append(operation)
        operation.run()

        return operation.response()

    def subscribe(self, address: str, service_uuid: str, char_uuid: str) -> tuple[Response, int]:
        """ Subscribe to a characteristic of a device """
        if address not in self.conn_reqs:
            return jsonify({"status": "FAILURE", "reason": "not connected"}), HTTPStatus.BAD_REQUEST

        conn_req = self.conn_reqs[address]
        handle = conn_req.handle

        service = conn_req.services[service_uuid]
        characteristic = service.characteristics[char_uuid]

        operation = SubscribeOperation(
            self.lib, handle, characteristic.char_handle, characteristic.properties,
            address,
            service_uuid,
            char_uuid,
            self.data_producer)
        self.operations.append(operation)
        operation.run()

        return operation.response()

    def unsubscribe(self, address: str, service_uuid: str, char_uuid: str) -> tuple[Response, int]:
        """ Unsubscribe from a characteristic of a device """
        if address not in self.conn_reqs:
            return jsonify({"status": "FAILURE", "reason": "not connected"}), HTTPStatus.BAD_REQUEST

        conn_req = self.conn_reqs[address]
        handle = conn_req.handle

        service = conn_req.services[service_uuid]
        characteristic = service.characteristics[char_uuid]

        # find the subscription operation
        for operation in self.operations:
            charhandle_match = operation.char_handle == characteristic.char_handle
            chk_handle = operation.handle == handle
            if isinstance(operation, SubscribeOperation) and chk_handle and charhandle_match:
                operation.disable_notification()
                return operation.response()

        return jsonify({"status": "FAILURE", "reason": "not subscribed"}), HTTPStatus.BAD_REQUEST

    def disconnect(self, address: str) -> tuple[Response, int]:
        """ Disconnect from a device """
        handle = self.conn_reqs[address].handle

        operation = DisconnectOperation(self.lib, handle)
        self.operations.append(operation)
        operation.run()

        return operation.response()

    def bt_evt_system_boot(self, evt):
        """ do a system boot and set configurations"""
        self.log.info("System booted")
        self.ready.set()

    def bt_evt_connection_closed(self, evt):
        """ function bt_evt_connection_closed """
        for address, conn_req in self.conn_reqs.items():
            if conn_req.handle == evt.connection:
                self.conn_reqs.pop(address)
                break

    def event_handler(self, evt):
        """ function to define actions based on different events """
        remove_ops: list[Operation] = []

        for operation in self.operations:
            operation.handle_event(evt)
            if operation.is_done:
                remove_ops.append(operation)

        for operation in remove_ops:
            self.operations.remove(operation)


ble_app: AccessPoint = None  # type: ignore


def create_ble_app(data_producer: DataProducer) -> AccessPoint:
    """ function to create BLE app """
    connector = get_connector()
    ble_app = AccessPoint(connector, data_producer)
    return ble_app


def get_ble_app() -> AccessPoint:
    """ Retrieves the existing BLE application. """
    return ble_app
