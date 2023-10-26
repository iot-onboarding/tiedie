# Copyright (c) 2023, Cisco and/or its affiliates.
# All rights reserved.
# See license in distribution for details.

"""

Class for reading data from a Bluetooth Low Energy (BLE) characteristic, 
handling responses, and generating success or failure messages.

"""

import uuid
from http import HTTPStatus
from flask import Response, jsonify
import bgapi
from silabs.ble_operations.operation import Operation


class ReadOperation(Operation):
    """ ReadOperation class for reading a BLE characteristic with response generation. """
    value: str

    def __init__(self, lib: bgapi.BGLib, handle: int, char_handle: int):
        super().__init__(lib)
        self.handle = handle
        self.char_handle = char_handle

    def run(self):
        """ run function """
        self.log.info(
            "reading characteristic %d from %d", self.char_handle, self.handle)
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
            json_arg = jsonify(
                {"status": "SUCCESS", "requestID": uuid.uuid4(), "value": self.value})
            return json_arg, HTTPStatus.OK

        return jsonify({"status": "FAILURE"}), HTTPStatus.BAD_REQUEST

    def __repr__(self):
        return f"ReadOperation({self.handle})"
