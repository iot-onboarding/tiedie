# Copyright (c) 2023, Cisco and/or its affiliates.
# All rights reserved.
# See license in distribution for details.

"""

This script defines BLE communication. Manages device connections, 
actions like scanning, reading/writing, and subscribing/unsubscribing 
to characteristics.

"""

import dataclasses
import threading
import logging
from flask import Response

from data_producer import DataProducer
from silabs.ble_operations.discover import Service


@dataclasses.dataclass
class ConnectionRequest:
    """ class containing attributes for a connection request """
    address: str
    handle: int
    services: dict[str, Service]


class AccessPoint:
    """ AccessPoint base class """

    # map of addresses to connection handles
    conn_reqs: dict[str, ConnectionRequest] = {}

    def __init__(self, data_producer: DataProducer):
        self.data_producer = data_producer
        self.ready = threading.Event()
        self.log = logging.getLogger()

    def start(self):
        """ Start the access point """
        raise NotImplementedError()

    def stop(self):
        """ Stop the access point """
        raise NotImplementedError()

    def connectable(self):
        """ Check if new connections can be established """
        raise NotImplementedError()

    def start_scan(self):
        """ Start scanning for devices """
        raise NotImplementedError()

    def connect(self, address, services, retries=3) -> tuple[Response, int]:
        """ Connect to a device """
        raise NotImplementedError()

    def discover(self, address, retries) -> tuple[Response, int]:
        """ Discover services of a device """
        raise NotImplementedError()

    def read(self, address: str, service_uuid: str, char_uuid: str) -> tuple[Response, int]:
        """ Read a characteristic of a device """
        raise NotImplementedError()

    def write(self,
              address: str,
              service_uuid: str,
              char_uuid: str,
              value: str) -> tuple[Response, int]:
        """ Write a characteristic of a device """
        raise NotImplementedError()

    def subscribe(self, address: str, service_uuid: str, char_uuid: str) -> tuple[Response, int]:
        """ Start a GATT notification/indication of a device """
        raise NotImplementedError()

    def unsubscribe(self, address: str, service_uuid: str, char_uuid: str) -> tuple[Response, int]:
        """ Stop a GATT notification/indication of a device """
        raise NotImplementedError()

    def disconnect(self, address: str) -> tuple[Response, int]:
        """ Disconnect a device """
        raise NotImplementedError()
