# Copyright (c) 2023, Cisco Systems, Inc. and/or its affiliates.
# All rights reserved.
# See LICENSE file in this distribution.
# SPDX-License-Identifier: Apache-2.0

"""

Class for writing data to a Bluetooth Low Energy (BLE) characteristic,
part of a BLE communication application. Handles write operations and
responses.

"""

import bgapi
from silabs.ble_operations.operation import Operation
from access_point_responses import WriteResponse


class WriteOperation(Operation):
    """ Handles writing a value to a BLE characteristic. """

    def __init__(self, lib: bgapi.BGLib, handle: int, char_handle: int, value: bytes):
        super().__init__(lib)
        self.handle = handle
        self.char_handle = char_handle
        self.value_bytes = value

    def run(self):
        self.log.info(
            "writing characteristic %d from %d", self.char_handle, self.handle)
        self.lib.bt.gatt.write_characteristic_value(  # type: ignore
            self.handle, self.char_handle, self.value_bytes)

        self.wait()

    def bt_evt_gatt_procedure_completed(self, evt):
        if self.handle == evt.connection:
            self.log.info(evt)
            self.set()
            self.is_done = True

    def response(self):
        if self.is_set():
            return WriteResponse(address=str(self.handle), service_uuid="", char_uuid="", value=self.value_bytes, success=True)
        return WriteResponse(address=str(self.handle), service_uuid="", char_uuid="", value=None, success=False)

    def __repr__(self):
        return f"WriteOperation({self.handle})"
