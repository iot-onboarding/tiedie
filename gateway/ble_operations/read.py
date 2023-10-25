# Copyright (c) 2023, Cisco and/or its affiliates.
# All rights reserved.
# See license in distribution for details.

import uuid
from http import HTTPStatus
from flask import Response, jsonify
from ble_operations.operation import Operation
import bgapi


class ReadOperation(Operation):
    def __init__(self, lib: bgapi.BGLib, handle: int, char_handle: int):
        super().__init__(lib)
        self.handle = handle
        self.char_handle = char_handle

    def run(self):
        self.log.info(
            f"reading characteristic {self.char_handle} from {self.handle}")
        self.lib.bt.gatt.read_characteristic_value(  # type: ignore
            self.handle, self.char_handle)

        self.wait()

    def bt_evt_gatt_characteristic_value(self, evt):
        if self.handle == evt.connection and \
                self.char_handle == evt.characteristic and \
                evt.att_opcode == self.lib.bt.gatt.ATT_OPCODE_READ_RESPONSE:  # type: ignore
            self.log.info(evt)
            self.value = evt.value.hex()
            self.set()

    def bt_evt_gatt_procedure_completed(self, evt):
        if self.handle == evt.connection:
            self.log.info(evt)
            self.is_done = True

    def response(self) -> tuple[Response, int]:
        if self.is_set():
            return jsonify({"status": "SUCCESS", "id": "", "requestID": uuid.uuid4(), "value": self.value}), HTTPStatus.OK

        return jsonify({"status": "FAILURE"}), HTTPStatus.BAD_REQUEST

    def __repr__(self):
        return f"ReadOperation({self.handle})"