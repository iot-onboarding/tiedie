# Copyright (c) 2023, Cisco Systems, Inc. and/or its affiliates.
# All rights reserved.
# See LICENSE file in this distribution.
# SPDX-License-Identifier: Apache-2.0

"""

Class for reading data from a Bluetooth Low Energy (BLE) characteristic,
handling responses, and generating success or failure messages.

"""

import bgapi
from silabs.ble_operations.operation import Operation
from access_point_responses import ReadResponse


class ReadOperation(Operation):
    """ ReadOperation class for reading a BLE characteristic with response generation. """
    value: bytes

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
            self.value = evt.value
            self.set()

    def bt_evt_gatt_procedure_completed(self, evt):
        """ Handles BLE procedure completion events, marking the operation as done. """
        if self.handle == evt.connection:
            self.log.info(evt)
            self.is_done = True

    def response(self):
        if self.is_set():
            return ReadResponse(address=str(self.handle), service_uuid="", char_uuid="", value=self.value)
        return ReadResponse(address=str(self.handle), service_uuid="", char_uuid="", value=None)

    def __repr__(self):
        return f"ReadOperation({self.handle})"
