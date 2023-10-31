# Copyright (c) 2023, Cisco and/or its affiliates.
# All rights reserved.
# See LICENSE file in this distribution.
# SPDX-License-Identifier: Apache-2.0

"""

Class for reading data from a Bluetooth Low Energy (BLE) characteristic, 
handling responses, and generating success or failure messages.

"""

import uuid
from http import HTTPStatus
from flask import Response, jsonify
import bgapi
from ble_operations.operation import Operation


class ReadOperation(Operation):
    """ ReadOperation class for reading a BLE characteristic with response generation. """
    def __init__(self, lib: bgapi.BGLib, handle: int, char_handle: int):
        super().__init__(lib)
        self.handle = handle
        self.char_handle = char_handle

    def run(self):
        """ run function """
        self.log.info(
            f"reading characteristic {self.char_handle} from {self.handle}")
        self.lib.bt.gatt.read_characteristic_value(  # type: ignore
            self.handle, self.char_handle)

        self.wait()

    def bt_evt_gatt_characteristic_value(self, evt):
        """ Handles BLE characteristic value events, setting the value. """
        if self.handle == evt.connection and \
                self.char_handle == evt.characteristic and \
                evt.att_opcode == self.lib.bt.gatt.ATT_OPCODE_READ_RESPONSE:  # type: ignore
            self.log.info(evt)
            self.value = evt.value.hex()
            self.set()

    def bt_evt_gatt_procedure_completed(self, evt):
        """ Handles BLE procedure completion events, marking the operation as done. """
        if self.handle == evt.connection:
            self.log.info(evt)
            self.is_done = True

    def response(self) -> tuple[Response, int]:
        """ response function """
        if self.is_set():
            return jsonify({"status": "SUCCESS", "id": "", "requestID": uuid.uuid4(), "value": self.value}), HTTPStatus.OK

        return jsonify({"status": "FAILURE"}), HTTPStatus.BAD_REQUEST

    def __repr__(self):
        return f"ReadOperation({self.handle})"
