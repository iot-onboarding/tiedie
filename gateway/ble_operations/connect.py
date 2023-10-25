# Copyright (c) 2023, Cisco and/or its affiliates.
# All rights reserved.
# See license in distribution for details.

from http import HTTPStatus
from flask import Response, jsonify
from ble_operations.operation import Operation
import bgapi

from config import CONNECTION_TIMEOUT
from data_producer import DataProducer


class ConnectOperation(Operation):
    def __init__(self, lib: bgapi.BGLib, data_producer: DataProducer, address: str, services, retries: int):
        super().__init__(lib)
        self.handle = 0
        self.address = address.lower()
        self.services = services
        self.retries = retries
        self.data_producer = data_producer

    def run(self):
        address_type = self.lib.bt.gap.ADDRESS_TYPE_STATIC_ADDRESS  # type: ignore

        if (self.__is_public_address(self.address)):
            address_type = self.lib.bt.gap.ADDRESS_TYPE_PUBLIC_ADDRESS  # type: ignore

        retries = 0

        for _ in range(self.retries + 1):
            _, self.handle = self.lib.bt.connection.open(  # type: ignore
                self.address, address_type, self.lib.bt.gap.PHY_PHY_1M)  # type: ignore

            if not self.wait(timeout=CONNECTION_TIMEOUT):
                retries += 1
                self.log.warning(
                    f"failed to open connection to {self.address}")
                self.lib.bt.connection.close(self.handle)  # type: ignore
            else:
                break

        # Reached max retries and failed to open connection
        if retries == self.retries + 1:
            self.is_done = True

    def bt_evt_connection_opened(self, evt):
        if self.handle == evt.connection:
            self.log.info(f"Connection opened: {evt.address}")
            self.set()

    def bt_evt_connection_closed(self, evt):
        if self.handle == evt.connection:
            self.log.info(evt)
            # is true if connection was opened before
            if self.is_set():
                self.is_done = True

    def response(self) -> tuple[Response, int]:
        if self.is_set():
            return jsonify({"status": "SUCCESS", "handle": self.handle}), HTTPStatus.OK

        return jsonify({"status": "FAILURE"}), HTTPStatus.BAD_REQUEST

    def __is_public_address(self, address: str) -> bool:
        first_byte = int(address[0:2], 16)
        # check if first byte is C0
        return (first_byte & 0xC0) != 0xC0

    def __repr__(self):
        return f"ConnectOperation({self.handle}, {self.address})"
