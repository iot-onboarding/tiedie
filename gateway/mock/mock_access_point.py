# Copyright (c) 2023, Cisco Systems, Inc. and/or its affiliates.
# All rights reserved.
# See LICENSE file in this distribution.
# SPDX-License-Identifier: Apache-2.0

"""
Mock AccessPoint class
"""

import dataclasses
from http import HTTPStatus
import random
import threading
import time
import uuid
from flask import Response, jsonify
from mock.mock_data import mock_advertisements
from access_point import AccessPoint, BleConnectOptions, ConnectionRequest
from data_producer import DataProducer


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
        self._subscription_threads: dict[(
            str, str, str), threading.Thread] = {}

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
                address,
                ble_connect_options: BleConnectOptions,
                retries=3) -> tuple[Response, int]:
        if not self.connectable():
            return jsonify({
                "status": "FAILURE",
                "requestID": uuid.uuid4(),
                "reason": "max connections"
            }), HTTPStatus.BAD_REQUEST

        if address in self.conn_reqs:
            return jsonify({
                "status": "FAILURE",
                "requestID": uuid.uuid4(),
                "reason": "already connected"
            }), HTTPStatus.BAD_REQUEST

        self.conn_reqs[address] = ConnectionRequest(address, 0, {})
        self.data_producer.publish_connection_status(
            ConnectionEvent(0), address, True)

        return jsonify({
            "status": "SUCCESS",
            "requestID": uuid.uuid4(),
            "services": [
                {
                    "serviceID": "180d",
                    "characteristics": [
                        {
                            "characteristicID": "2a37",
                            "flags": ["notify"],
                            "descriptors": [
                                {
                                    "descriptorID": "2902"
                                }
                            ]
                        },
                        {
                            "characteristicID": "2a38",
                            "flags": ["read"]
                        },
                        {
                            "characteristicID": "2a39",
                            "flags": ["write"]
                        }
                    ]
                }
            ]
        }), HTTPStatus.OK

    def discover(self,
                 address,
                 ble_connect_options: BleConnectOptions,
                 retries=3) -> tuple[Response, int]:
        if address not in self.conn_reqs:
            return jsonify({"status": "FAILURE", "reason": "not connected"}), HTTPStatus.BAD_REQUEST

        return jsonify({
            "status": "SUCCESS",
            "requestID": uuid.uuid4(),
            "services": [
                {
                    "serviceID": "180d",
                    "characteristics": [
                        {
                            "characteristicID": "2a37",
                            "flags": ["notify"],
                            "descriptors": [
                                {
                                    "descriptorID": "2902"
                                }
                            ]
                        },
                        {
                            "characteristicID": "2a38",
                            "flags": ["read"]
                        },
                        {
                            "characteristicID": "2a39",
                            "flags": ["write"]
                        }
                    ]
                }
            ]
        }), HTTPStatus.OK

    def read(self, address: str, service_uuid: str, char_uuid: str) -> tuple[Response, int]:
        if address not in self.conn_reqs:
            return jsonify({"status": "FAILURE", "reason": "not connected"}), HTTPStatus.BAD_REQUEST

        if service_uuid != "180d" or char_uuid != "2a38":
            return jsonify({
                "status": "FAILURE",
                "reason": "Invalid service or characteristic uuid"
            }), HTTPStatus.BAD_REQUEST

        return jsonify({
            "status": "SUCCESS",
            "requestID": uuid.uuid4(),
            "value": "000001"
        }), HTTPStatus.OK

    def write(self,
              address: str,
              service_uuid: str,
              char_uuid: str,
              value: str) -> tuple[Response, int]:
        if address not in self.conn_reqs:
            return jsonify({"status": "FAILURE", "reason": "not connected"}), HTTPStatus.BAD_REQUEST

        if service_uuid != "180d" or char_uuid != "2a39":
            return jsonify({
                "status": "FAILURE",
                "reason": "Invalid service or characteristic uuid"
            }), HTTPStatus.BAD_REQUEST

        return jsonify({
            "status": "SUCCESS",
            "requestID": uuid.uuid4(),
            "value": value
        }), HTTPStatus.OK

    def subscribe(self, address: str, service_uuid: str, char_uuid: str) -> tuple[Response, int]:
        if address not in self.conn_reqs:
            return jsonify({"status": "FAILURE", "reason": "not connected"}), HTTPStatus.BAD_REQUEST

        thread = threading.Thread(
            target=self._send_subscribe_data, args=(address, service_uuid, char_uuid))
        thread.start()

        self._subscription_threads[(address, service_uuid, char_uuid)] = thread

        return jsonify({"status": "SUCCESS", "requestID": uuid.uuid4()}), HTTPStatus.OK

    def unsubscribe(self, address: str, service_uuid: str, char_uuid: str) -> tuple[Response, int]:
        thread = self._subscription_threads[(address, service_uuid, char_uuid)]
        self._subscription_threads.pop((address, service_uuid, char_uuid))
        thread.join()

        return jsonify({"status": "SUCCESS", "requestID": uuid.uuid4()}), HTTPStatus.OK

    def _send_subscribe_data(self, address, service_uuid, char_uuid):
        while (address, service_uuid, char_uuid) in self._subscription_threads:
            self.data_producer.publish_notification(
                address,
                service_uuid,
                char_uuid,
                (0xFFFF0000 + random.randint(0, 0xFFFF)).to_bytes(4, byteorder="big")
            )
            time.sleep(1)

    def disconnect(self, address: str) -> tuple[Response, int]:
        if address not in self.conn_reqs:
            return jsonify({"status": "FAILURE", "reason": "not connected"}), HTTPStatus.BAD_REQUEST

        self.conn_reqs.pop(address)
        self.data_producer.publish_connection_status(
            ConnectionEvent(1), address, False)

        return jsonify({
            "status": "SUCCESS",
            "requestID": uuid.uuid4()
        }), HTTPStatus.OK
