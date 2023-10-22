# Copyright (c) 2023, Cisco and/or its affiliates.
# All rights reserved.
# See license in distribution for details.

from http import HTTPStatus
from flask import Response, jsonify
from ble_operations.operation import Operation
import bgapi

from config import CONNECTION_TIMEOUT


class DisconnectOperation(Operation):
    def __init__(self, lib: bgapi.BGLib, handle: int):
        super().__init__(lib)
        self.handle = handle

    def run(self):
        self.lib.bt.connection.close(self.handle)  # type: ignore
        if not self.wait(timeout=CONNECTION_TIMEOUT):
            self.log.warning(f"failed to close connection to {self.handle}")

    def bt_evt_connection_closed(self, evt):
        if self.handle == evt.connection:
            self.log.info(evt)
            self.is_done = True
            self.set()

    def response(self) -> tuple[Response, int]:
        if self.is_set():
            return jsonify({"status": "SUCCESS"}), HTTPStatus.OK

        return jsonify({"status": "FAILURE"}), HTTPStatus.BAD_REQUEST

    def __repr__(self):
        return f"DisconnectOperation({self.handle})"
