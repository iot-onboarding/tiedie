# Copyright (c) 2023, Cisco and/or its affiliates.
# All rights reserved.
# See LICENSE file in this distribution.
# SPDX-License-Identifier: Apache-2.0

import uuid
from http import HTTPStatus
from flask import Response, jsonify
from ble_operations.operation import Operation
import bgapi


class WriteOperation(Operation):
    def __init__(self, lib: bgapi.BGLib, handle: int, char_handle: int, value: str):
        super().__init__(lib)
        self.handle = handle
        self.char_handle = char_handle
        self.value = value
        self.value_bytes = bytes.fromhex(value)

    def run(self):
        self.log.info(
            f"writing characteristic {self.char_handle} from {self.handle}")
        self.lib.bt.gatt.write_characteristic_value(  # type: ignore
            self.handle, self.char_handle, self.value_bytes)

        self.wait()

    def bt_evt_gatt_procedure_completed(self, evt):
        if self.handle == evt.connection:
            self.log.info(evt)
            self.set()
            self.is_done = True

    def response(self) -> tuple[Response, int]:
        if self.is_set():
            return jsonify({"status": "SUCCESS", "id": "", "requestID": uuid.uuid4(), "value": self.value}), HTTPStatus.OK

        return jsonify({"status": "FAILURE"}), HTTPStatus.BAD_REQUEST

    def __repr__(self):
        return f"ReadOperation({self.handle})"
