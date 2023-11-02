
# Copyright (c) 2023, Cisco and/or its affiliates.
# All rights reserved.
# See LICENSE file in this distribution.
# SPDX-License-Identifier: Apache-2.0

"""

`ConnectOperation` class manages Bluetooth connections, handles events,
provides response data, and is part of a larger system/application.

"""

from http import HTTPStatus
from flask import Response, jsonify
import bgapi
from silabs.ble_operations.operation import Operation

from config import CONNECTION_TIMEOUT
from data_producer import DataProducer


class ConnectOperation(Operation):
    """ Connects to a device and manages connection status. """

    def __init__(self, lib: bgapi.BGLib,
                 data_producer: DataProducer,
                 address: str,
                 retries: int):
        super().__init__(lib)
        self.handle = 0
        self.address = address.lower()
        self.retries = retries
        self.data_producer = data_producer

    def run(self):
        """ Connects with retries using specified address type """
        address_type = self.lib.bt.gap.ADDRESS_TYPE_STATIC_ADDRESS  # type: ignore

        if self.__is_public_address(self.address):
            address_type = self.lib.bt.gap.ADDRESS_TYPE_PUBLIC_ADDRESS  # type: ignore

        retries = 0

        for _ in range(self.retries + 1):
            _, self.handle = self.lib.bt.connection.open(  # type: ignore
                self.address, address_type, self.lib.bt.gap.PHY_PHY_1M)  # type: ignore

            if not self.wait(timeout=CONNECTION_TIMEOUT):
                retries += 1
                self.log.warning(
                    "failed to open connection to %s", self.address)
                self.lib.bt.connection.close(self.handle)  # type: ignore
            else:
                break

        # Reached max retries and failed to open connection
        if retries == self.retries + 1:
            self.is_done = True

    def bt_evt_connection_opened(self, evt):
        """ Handles connection opened event, logs it, and sets the status. """
        if self.handle == evt.connection:
            self.log.info("Connection opened: %s", evt.address)
            self.data_producer.publish_connection_status(
                evt, self.address, True)
            self.set()

    def bt_evt_connection_closed(self, evt):
        """ Handles connection closed event, logs it, and sets status if needed. """
        if self.handle == evt.connection:
            self.log.info(evt)
            self.data_producer.publish_connection_status(
                evt, self.address, False)
            # is true if connection was opened before
            if self.is_set():
                self.is_done = True

    def response(self) -> tuple[Response, int]:
        """ Returns a success response with handle if set, otherwise failure. """
        if self.is_set():
            return jsonify({"status": "SUCCESS", "handle": self.handle}), HTTPStatus.OK

        return jsonify({"status": "FAILURE"}), HTTPStatus.BAD_REQUEST

    def __is_public_address(self, address: str) -> bool:
        first_byte = int(address[0:2], 16)
        # check if first byte is C0
        return (first_byte & 0xC0) != 0xC0

    def __repr__(self):
        return f"ConnectOperation({self.handle}, {self.address})"
