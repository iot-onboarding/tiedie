# Copyright (c) 2023, Cisco Systems, Inc. and/or its affiliates.
# All rights reserved.
# See LICENSE file in this distribution.
# SPDX-License-Identifier: Apache-2.0

"""

DisconnectOperation class manages Bluetooth disconnections, handles events, 
provides response data, and is part of a larger system/application.

"""

from http import HTTPStatus
from flask import Response, jsonify
import bgapi
from ble_operations.operation import Operation

from config import CONNECTION_TIMEOUT


class DisconnectOperation(Operation):
    """ DisconnectOperation class manages disconnections using the BGAPI library. """
    def __init__(self, lib: bgapi.BGLib, handle: int):
        super().__init__(lib)
        self.handle = handle

    def run(self):
        """ run """
        self.lib.bt.connection.close(self.handle)  # type: ignore
        if not self.wait(timeout=CONNECTION_TIMEOUT):
            self.log.warning(f"failed to close connection to {self.handle}")

    def bt_evt_connection_closed(self, evt):
        """ 
        This method handles Bluetooth connection closure events by 
        setting the operation as done and logging event information. 
        """
        if self.handle == evt.connection:
            self.log.info(evt)
            self.is_done = True
            self.set()

    def response(self) -> tuple[Response, int]:
        """ return response """
        if self.is_set():
            return jsonify({"status": "SUCCESS"}), HTTPStatus.OK

        return jsonify({"status": "FAILURE"}), HTTPStatus.BAD_REQUEST

    def __repr__(self):
        return f"DisconnectOperation({self.handle})"
