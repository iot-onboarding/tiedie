# Copyright (c) 2023, Cisco Systems, Inc. and/or its affiliates.
# All rights reserved.
# See LICENSE file in this distribution.
# SPDX-License-Identifier: Apache-2.0

"""
Mock AccessPoint class
"""

import dataclasses
import random
import threading
import time
from access_point import AccessPoint, BleConnectOptions, ConnectionRequest
from data_producer import DataProducer
from mock.mock_data import mock_advertisements

from access_point_responses import (
    BleConnectionError, BleDiscoveryError, DiscoverResponse,
    BleReadError, ReadResponse, BleSubscribeError, SubscribeResponse,
    BleDisconnectError, BleWriteError, UnsubscribeResponse, WriteResponse
)
from ble_types import Service, Characteristic, Descriptor


@dataclasses.dataclass
class Advertisement:
    """ Advertisement class for publishing """
    address: str
    rssi: int
    data: bytes


@dataclasses.dataclass
class ConnectionEvent:
    """ Mock connection event """
    reason: int


class MockAccessPoint(AccessPoint):
    """ Mock AccessPoint class"""

    scan_thread: threading.Thread

    def __init__(self, data_producer: DataProducer):
        super().__init__(data_producer)
        self._scanning = False
        self._subscription_threads: dict[tuple[str, str, str], threading.Thread] = {}

    def start(self):
        self.log.info("System booted")
        self.ready.set()

    def stop(self):
        self.log.info("Stopping...")
        self._scanning = False
        self.scan_thread.join()

    def connectable(self):
        return True

    def start_scan(self):
        # Generate advertisement events
        self._scanning = True
        self.scan_thread = threading.Thread(target=self._send_scan_data)
        self.scan_thread.start()

    def _send_scan_data(self):
        while self._scanning:
            i = 0
            for adv in mock_advertisements:
                self.data_producer.publish_advertisement(
                    Advertisement(
                        f"C1:5C:00:00:00:{i:02}",
                        random.randint(-30, -20),
                        bytes.fromhex(adv)
                    )
                )
                i += 1

    def connect(self,
                address: str,
                _ble_connect_options: BleConnectOptions,
                _retries: int = 3) -> None:
        if not self.connectable():
            raise BleConnectionError("max connections")

        if address in self.conn_reqs:
            raise BleConnectionError("already connected")

        self.conn_reqs[address] = ConnectionRequest(address, 0, {})
        self.data_producer.publish_connection_status(
            ConnectionEvent(0), address, True)

    def discover(self,
                 address: str,
                 _ble_connect_options: BleConnectOptions,
                 _retries: int = 3) -> DiscoverResponse:
        if address not in self.conn_reqs:
            raise BleDiscoveryError("not connected")

        # Create mock Service/Characteristic/Descriptor objects
        char1 = Characteristic("2a37", 1, 0x10)  # notify
        char1.descriptors["2902"] = Descriptor("2902", 1)
        char2 = Characteristic("2a38", 2, 0x02)  # read
        char3 = Characteristic("2a39", 3, 0x08)  # write
        service = Service(
            service_id="180d",
            service_handle=1,
            characteristics={
                "2a37": char1,
                "2a38": char2,
                "2a39": char3
            }
        )
        services = [service]
        return DiscoverResponse(address=address, services=services)

    def read(self, address: str, service_uuid: str, char_uuid: str) -> ReadResponse:
        if address not in self.conn_reqs:
            raise BleReadError("not connected")

        if service_uuid != "180d" or char_uuid != "2a38":
            raise BleReadError("Invalid service or characteristic uuid")

        value = b"test"  # mock value
        return ReadResponse(
            address=address,
            service_uuid=service_uuid,
            char_uuid=char_uuid,
            value=value
        )

    def write(self,
              address: str,
              service_uuid: str,
              char_uuid: str,
              value: bytes) -> WriteResponse:
        # Accept any write in mock
        if address not in self.conn_reqs:
            raise BleWriteError("not connected")

        return WriteResponse(
            address=address,
            service_uuid=service_uuid,
            char_uuid=char_uuid,
            value=value,
            success=True
        )

    def subscribe(self, address: str, service_uuid: str, char_uuid: str) -> SubscribeResponse:
        if address not in self.conn_reqs:
            raise BleSubscribeError("not connected")

        key = (address, service_uuid, char_uuid)
        if key in self._subscription_threads:
            raise BleSubscribeError("already subscribed")

        thread = threading.Thread(
            target=self._send_subscribe_data,
            args=(address, service_uuid, char_uuid)
        )
        self._subscription_threads[key] = thread
        thread.start()

        return SubscribeResponse(
            address=address,
            service_uuid=service_uuid,
            char_uuid=char_uuid,
            subscribed=True
        )

    def unsubscribe(self, address: str, service_uuid: str, char_uuid: str) -> UnsubscribeResponse:
        key = (address, service_uuid, char_uuid)
        if key not in self._subscription_threads:
            raise BleSubscribeError("not subscribed")

        thread = self._subscription_threads[key]
        self._subscription_threads.pop(key)
        thread.join()

        return UnsubscribeResponse(
            address=address,
            service_uuid=service_uuid,
            char_uuid=char_uuid,
            unsubscribed=True
        )

    def _send_subscribe_data(self, address, service_uuid, char_uuid):
        while (address, service_uuid, char_uuid) in self._subscription_threads:
            self.data_producer.publish_notification(
                address,
                service_uuid,
                char_uuid,
                (0xFFFF0000 + random.randint(0, 0xFFFF)).to_bytes(4, byteorder="big")
            )
            time.sleep(1)

    def disconnect(self, address: str) -> None:
        """Mock disconnect, always succeeds."""
        if address not in self.conn_reqs:
            raise BleDisconnectError("not connected")

        self.conn_reqs.pop(address)
        self.data_producer.publish_connection_status(
            ConnectionEvent(1), address, False)
