# Copyright (c) 2023, Cisco and/or its affiliates.
# All rights reserved.
# See license in distribution for details.

from http import HTTPStatus
import logging
import threading
import bgapi
from flask import Response, jsonify

class Operation(threading.Event):
    def __init__(self, lib: bgapi.BGLib):
        super().__init__()
        self.lib = lib
        self.is_done = False
        self.log = logging.getLogger()

    def run(self):
        pass

    def handle_event(self, evt):
        event_callback = getattr(self, evt._str, None)
        if event_callback is not None:
            event_callback(evt)

    def response(self) -> tuple[Response, int]:
        return jsonify({}), HTTPStatus.OK