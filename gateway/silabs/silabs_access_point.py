# Copyright (c) 2023, Cisco Systems, Inc. and/or its affiliates.
# All rights reserved.
# See LICENSE file in this distribution.
# SPDX-License-Identifier: Apache-2.0

"""
Silabs Access Point class
"""

from data_producer import DataProducer
from silabs.ble_operations.connect import ConnectOperation
from silabs.ble_operations.disconnect import DisconnectOperation
from silabs.ble_operations.discover import DiscoverOperation
from silabs.ble_operations.operation import Operation
from silabs.ble_operations.read import ReadOperation
from silabs.ble_operations.scan import ScanOperation
from silabs.ble_operations.subscribe import SubscribeOperation
from silabs.ble_operations.write import WriteOperation
from silabs.common.util import BluetoothApp
from config import SL_BT_CONFIG_MAX_CONNECTIONS
from access_point import AccessPoint, BleConnectOptions, ConnectionRequest
from access_point_responses import BleConnectionError, BleDisconnectError, BleDiscoveryError, BleReadError, BleSubscribeError, BleUnsubscribeError, BleWriteError, DiscoverResponse, ReadResponse, SubscribeResponse, UnsubscribeResponse, WriteResponse

class SilabsAccessPoint(AccessPoint):
    """ Manages Bluetooth Low Energy (BLE) operations and connections."""

    operations: list[Operation] = []

    def __init__(self, connector, data_producer: DataProducer):
        super().__init__(data_producer)
        self.silabs_app = BluetoothApp(connector)
        self.silabs_app.event_handler = self.event_handler

    def start(self):
        """ Start the Bluetooth application """
        self.silabs_app.start()

    def stop(self):
        """ Stop the Bluetooth application """
        self.silabs_app.stop()

    def connectable(self):
        """ Check if new connections can be established """
        return len(self.conn_reqs) < SL_BT_CONFIG_MAX_CONNECTIONS

    def start_scan(self):
        """ Start scanning for devices """
        scan_operation = ScanOperation(self.silabs_app.lib, self.data_producer)
        self.operations.append(scan_operation)
        scan_operation.run()

    def connect(self,
                address: str,
                ble_connect_options: BleConnectOptions,
                retries: int = 3) -> None:
        """ Establish a connection to a BLE device """
        if not self.connectable():
            raise BleConnectionError("max connections")
        if address in self.conn_reqs:
            raise BleConnectionError("already connected")
        operation = ConnectOperation(
            self.silabs_app.lib, self.data_producer, address, retries)
        self.operations.append(operation)
        operation.run()

        if not operation.is_set():
            raise BleConnectionError("connection operation failed")
        else:
            self.conn_reqs[address] = ConnectionRequest(address, operation.handle, {})

    def discover(self,
                 address: str,
                 ble_connect_options: BleConnectOptions,
                 retries: int = 3) -> DiscoverResponse:
        """ Discover services of a connected BLE device """
        if address not in self.conn_reqs:
            raise BleDiscoveryError("not connected")

        discover_operation = DiscoverOperation(
            self.silabs_app.lib,
            self.conn_reqs[address].handle,
            retries,
            ble_connect_options.services
        )
        self.operations.append(discover_operation)

        discover_operation.run()

        self.conn_reqs[address].services = discover_operation.services

        return DiscoverResponse(address=address, services=discover_operation.services)

    def read(self, address: str, service_uuid: str, char_uuid: str) -> ReadResponse:
        """ Read a characteristic from a connected BLE device """
        if address not in self.conn_reqs:
            raise BleReadError("not connected")

        conn_req = self.conn_reqs[address]
        handle = conn_req.handle

        service = conn_req.services[service_uuid]
        characteristic = service.characteristics[char_uuid]

        operation = ReadOperation(
            self.silabs_app.lib, handle, characteristic.char_handle)
        self.operations.append(operation)
        operation.run()

        return operation.response()

    def write(self,
              address: str,
              service_uuid: str,
              char_uuid: str,
              value: bytes) -> WriteResponse:
        """ Write a value to a characteristic of a connected BLE device """
        if address not in self.conn_reqs:
            raise BleWriteError("not connected")

        conn_req = self.conn_reqs[address]
        handle = conn_req.handle

        service = conn_req.services[service_uuid]
        characteristic = service.characteristics[char_uuid]

        operation = WriteOperation(
            self.silabs_app.lib, handle, characteristic.char_handle, value)
        self.operations.append(operation)
        operation.run()

        # Assume success for now
        return WriteResponse(address=address, service_uuid=service_uuid, char_uuid=char_uuid, value=value, success=True)

    def subscribe(self, address: str, service_uuid: str, char_uuid: str) -> SubscribeResponse:
        """ Subscribe to notifications from a characteristic of a connected BLE device """
        if address not in self.conn_reqs:
            raise BleSubscribeError("not connected")

        conn_req = self.conn_reqs[address]
        handle = conn_req.handle

        service = conn_req.services[service_uuid]
        characteristic = service.characteristics[char_uuid]

        operation = SubscribeOperation(
            self.silabs_app.lib, handle, characteristic.char_handle, characteristic.properties,
            address,
            service_uuid,
            char_uuid,
            self.data_producer)
        self.operations.append(operation)
        operation.run()

        # Assume success for now
        return SubscribeResponse(address=address, service_uuid=service_uuid, char_uuid=char_uuid, subscribed=True)

    def unsubscribe(self, address: str, service_uuid: str, char_uuid: str) -> UnsubscribeResponse:
        """ Unsubscribe from notifications from a characteristic of a connected BLE device """
        if address not in self.conn_reqs:
            raise BleUnsubscribeError("not connected")

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
                return UnsubscribeResponse(address=address, service_uuid=service_uuid, char_uuid=char_uuid, unsubscribed=True)

        raise BleUnsubscribeError("not subscribed")

    def disconnect(self, address: str) -> None:
        """ Disconnect a device. Raises DisconnectError. """
        handle = self.conn_reqs[address].handle

        operation = DisconnectOperation(self.silabs_app.lib, handle)
        self.operations.append(operation)
        operation.run()

        if not operation.is_set():
            raise BleDisconnectError("disconnect operation failed")

    def bt_evt_system_boot(self, _evt):
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

        event_callback = getattr(
            self, evt._str, None)  # pylint: disable=protected-access
        if event_callback is not None:
            event_callback(evt)
