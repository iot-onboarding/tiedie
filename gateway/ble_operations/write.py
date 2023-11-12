# Copyright (c) 2023, Cisco Systems, Inc. and/or its affiliates.
# All rights reserved.
# See LICENSE file in this distribution.
# SPDX-License-Identifier: Apache-2.0

"""

Class for writing data to a Bluetooth Low Energy (BLE) characteristic,
part of a BLE communication application. Handles write operations and
responses.

"""

import uuid
from http import HTTPStatus
from flask import Response, jsonify
import bgapi
from ble_operations.operation import Operation

class WriteOperation(Operation):
    """ Handles writing a value to a BLE characteristic. """
    def __init__(self, lib: bgapi.BGLib, handle: int, char_handle: int, value: str):
        super().__init__(lib)
        self.handle = handle
        self.char_handle = char_handle
        self.value = value
        self.value_bytes = bytes.fromhex(value)

    def run(self):
        """ function run """
        self.log.info(
            f"writing characteristic {self.char_handle} from {self.handle}")
        self.lib.bt.gatt.write_characteristic_value(  # type: ignore
            self.handle, self.char_handle, self.value_bytes)

        self.wait()

    def bt_evt_gatt_procedure_completed(self, evt):
       """ Handles procedure completion events and sets the operation's state. """
       if self.handle == evt.connection:
            self.log.info(evt)
            self.set()
            self.is_done = True

    def response(self) -> tuple[Response, int]:
        """ Generates a response based on the operation's state and outcome. """
        if self.is_set():
            return jsonify({"status": "SUCCESS", "id": "", "requestID": uuid.uuid4(), "value": self.value}), HTTPStatus.OK

        return jsonify({"status": "FAILURE"}), HTTPStatus.BAD_REQUEST

    def __repr__(self):
        """ function ReadOperation """
        return f"ReadOperation({self.handle})"
