from dataclasses import dataclass
from typing import List
from ble_types import Service

@dataclass
class DiscoverResponse:
    address: str
    services: List[Service]

@dataclass
class ReadResponse:
    address: str
    service_uuid: str
    char_uuid: str
    value: bytes

@dataclass
class WriteResponse:
    address: str
    service_uuid: str
    char_uuid: str
    value: bytes
    success: bool

@dataclass
class SubscribeResponse:
    address: str
    service_uuid: str
    char_uuid: str
    subscribed: bool

@dataclass
class UnsubscribeResponse:
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
