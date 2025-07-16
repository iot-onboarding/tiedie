# Copyright (c) 2023, Cisco Systems, Inc. and/or its affiliates.
# All rights reserved.
# See LICENSE file in this distribution.
# SPDX-License-Identifier: Apache-2.0

"""

Class for background operations handling events and generating responses.

"""

import logging
import threading
import bgapi

class Operation(threading.Event):
    """ class for handling Bluetooth operations with response generation. """
    def __init__(self, lib: bgapi.BGLib):
        super().__init__()
        self.lib = lib
        self.is_done = False
        self.log = logging.getLogger()

    def run(self):
        """ run function """
        raise NotImplementedError()

    def handle_event(self, evt):
        """ handle_event function """
        event_callback = getattr(self, evt._str, None)  # pylint: disable=protected-access
        if event_callback is not None:
            event_callback(evt)

    def response(self):
        """ Returns a response object for the operation. """
        return None
