# Copyright (c) 2023, Cisco and/or its affiliates.
# All rights reserved.
# See LICENSE file in this distribution.
# SPDX-License-Identifier: Apache-2.0

"""

Class for subscribing to Bluetooth Low Energy (BLE) characteristic
notifications/indications, forwarding data, and managing notifications.

"""

from http import HTTPStatus
import uuid
import bgapi
from flask import Response, jsonify

from silabs.ble_operations.operation import Operation
from data_producer import DataProducer


class SubscribeOperation(Operation):
    """ Handles subscribing to a BLE characteristic, handling notifications and indications. """

    def __init__(self,
                 lib: bgapi.BGLib,
                 handle: int,
                 char_handle: int,
                 properties: list[str],
                 address: str,
                 service_uuid: str,
                 char_uuid: str,
                 data_producer: DataProducer):
        super().__init__(lib)
        self.handle = handle
        self.char_handle = char_handle
        self.properties = properties
        self.address = address
        self.service_uuid = service_uuid
        self.char_uuid = char_uuid
        self.data_producer = data_producer
        self.__disable = False

    def run(self):
        """ run Function """
        self.log.info(
            "subscribe to characteristic %d from %d", self.char_handle, self.handle)

        if "notify" in self.properties:
            flag = self.lib.bt.gatt.CLIENT_CONFIG_FLAG_NOTIFICATION  # type: ignore
        elif "indicate" in self.properties:
            flag = self.lib.bt.gatt.CLIENT_CONFIG_FLAG_INDICATION  # type: ignore
        else:
            self.log.error("No notify or indicate property")
            return

        self.lib.bt.gatt.set_characteristic_notification(  # type: ignore
            self.handle, self.char_handle, flag)

        self.wait()

    def bt_evt_gatt_characteristic_value(self, evt):
        """ Processes characteristic value notifications/indications. """
        if self.handle == evt.connection and \
                self.char_handle == evt.characteristic and \
                evt.att_opcode in (self.lib.bt.gatt.ATT_OPCODE_HANDLE_VALUE_NOTIFICATION,
                                   self.lib.bt.gatt.ATT_OPCODE_HANDLE_VALUE_INDICATION):  # type: ignore
            self.log.info(evt)
            if evt.att_opcode == self.lib.bt.gatt.ATT_OPCODE_HANDLE_VALUE_INDICATION:  # type: ignore
                try:
                    self.lib.bt.gatt.send_characteristic_confirmation(   # type: ignore
                        self.handle)
                except ImportError as error_exp:
                    self.log.error(error_exp)
                    # TODO: Why does this happen?
            self.data_producer.publish_notification(
                self.address, self.service_uuid, self.char_uuid, evt.value)

    def disable_notification(self):
        """ Disables notifications/indications for the characteristic. """
        self.clear()
        self.__disable = True
        self.lib.bt.gatt.set_characteristic_notification(  # type: ignore
            self.handle, self.char_handle, self.lib.bt.gatt.CLIENT_CONFIG_FLAG_DISABLE)  # type:ignore

        self.wait()

    def bt_evt_gatt_procedure_completed(self, evt):
        """ Handles procedure completion events and sets the operation's state. """
        if self.handle == evt.connection:
            self.set()
            if self.__disable:
                self.is_done = True

    def response(self) -> tuple[Response, int]:
        """ Response Function """
        if self.is_set():
            return jsonify({"status": "SUCCESS", "requestID": uuid.uuid4()}), HTTPStatus.OK

        return jsonify({"status": "FAILURE"}), HTTPStatus.BAD_REQUEST

    def __repr__(self):
        return f"{self.__class__.__name__}({self.handle})"
