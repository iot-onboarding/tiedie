# Copyright (c) 2023, Cisco Systems, Inc. and/or its affiliates.
# All rights reserved.
# See LICENSE file in this distribution.
# SPDX-License-Identifier: Apache-2.0

"""

This script defines BLE communication. Manages device connections,
actions like scanning, reading/writing, and subscribing/unsubscribing
to characteristics.

"""

import dataclasses
import threading
import logging
import abc
from typing import Optional

from data_producer import DataProducer
from access_point_responses import (
    DiscoverResponse, ReadResponse, WriteResponse,
    SubscribeResponse, UnsubscribeResponse
)

@dataclasses.dataclass
class Service:
    """
    This class represents a service in Bluetooth Low Energy (BLE)
    with a UUID and a service handle, containing characteristics as a
    dictionary.
    """
    service_id: str
    service_handle: int
    characteristics: dict[str, "Characteristic"] = dataclasses.field(
        default_factory=dict)


@dataclasses.dataclass
class ConnectionRequest:
    """ class containing attributes for a connection request """
    address: str
    handle: int
    services: dict[str, Service]


@dataclasses.dataclass
class BleConnectOptions:
    """ class containing attributes for a connection request """
    services: list[dict[str, str]] = dataclasses.field(default_factory=list)
    cached: bool = False
    cache_idle_purge: int = 3600


class AccessPoint:
    """ AccessPoint base class """

    # map of addresses to connection handles
    conn_reqs: dict[str, ConnectionRequest] = {}

    def __init__(self, data_producer: DataProducer):
        self.data_producer = data_producer
        self.ready = threading.Event()
        self.log = logging.getLogger()

    def get_connection(self, address: str) -> Optional[ConnectionRequest]:
        """ Get a connection request by address """
        return self.conn_reqs.get(address, None)

    @abc.abstractmethod
    def start(self):
        """ Start the access point """

    @abc.abstractmethod
    def stop(self):
        """ Stop the access point """

    @abc.abstractmethod
    def connectable(self):
        """ Check if new connections can be established """

    @abc.abstractmethod
    def start_scan(self):
        """ Start scanning for devices """

    @abc.abstractmethod
    def connect(self,
                address: str,
                ble_connect_options: BleConnectOptions,
                retries: int = 3) -> None:
        """Connect to a device. Returns None on success or raises ConnectionError on failure."""

    @abc.abstractmethod
    def discover(self,
                 address: str,
                 ble_connect_options: BleConnectOptions,
                 retries: int = 3) -> DiscoverResponse:
        """Discover services of a device. Returns a DiscoverResponse or raises DiscoveryError."""

    @abc.abstractmethod
    def read(self, address: str, service_uuid: str, char_uuid: str) -> ReadResponse:
        """Read a characteristic of a device. Returns a ReadResponse or raises ReadError."""

    @abc.abstractmethod
    def write(self,
              address: str,
              service_uuid: str,
              char_uuid: str,
              value: str) -> WriteResponse:
        """Write a characteristic of a device. Returns a WriteResponse or raises WriteError."""

    @abc.abstractmethod
    def subscribe(self, address: str, service_uuid: str, char_uuid: str) -> SubscribeResponse:
        """
        Start a GATT notification/indication of a device. 
        Returns a SubscribeResponse or raises SubscribeError.
        """

    @abc.abstractmethod
    def unsubscribe(self, address: str, service_uuid: str, char_uuid: str) -> UnsubscribeResponse:
        """
        Stop a GATT notification/indication of a device.
        Returns an UnsubscribeResponse or raises UnsubscribeError.
        """

    @abc.abstractmethod
    def disconnect(self, address: str) -> None:
        """Disconnect a device. Returns None on success or raises DisconnectError on failure."""
