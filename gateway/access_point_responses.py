"""

Class for responses from a Bluetooth Low Energy (BLE) access point,
part of a BLE communication application. Handles responses to write operations.

"""

from dataclasses import dataclass
from typing import List
from ble_types import Service

@dataclass
class DiscoverResponse:
    """Handles responses to discover operations."""
    address: str
    services: List[Service]

@dataclass
class ReadResponse:
    """Handles responses to read operations."""
    address: str
    service_uuid: str
    char_uuid: str
    value: bytes

@dataclass
class WriteResponse:
    """Handles responses to write operations."""
    address: str
    service_uuid: str
    char_uuid: str
    value: bytes
    success: bool

@dataclass
class SubscribeResponse:
    """Handles responses to subscribe operations."""
    address: str
    service_uuid: str
    char_uuid: str
    subscribed: bool

@dataclass
class UnsubscribeResponse:
    """Handles responses to unsubscribe operations."""
    address: str
    service_uuid: str
    char_uuid: str
    unsubscribed: bool

# Error types
class AccessPointError(Exception):
    """Base class for access point errors."""

class BleConnectionError(AccessPointError):
    """Error during BLE connection."""

class BleDiscoveryError(AccessPointError):
    """Error during BLE discovery."""

class BleReadError(AccessPointError):
    """Error during BLE read."""

class BleWriteError(AccessPointError):
    """Error during BLE write."""

class BleSubscribeError(AccessPointError):
    """Error during BLE subscribe."""

class BleUnsubscribeError(AccessPointError):
    """Error during BLE unsubscribe."""

class BleDisconnectError(AccessPointError):
    """Error during BLE disconnect."""
