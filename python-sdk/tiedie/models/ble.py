#!python
# Copyright (c) 2023, Cisco Systems, Inc. and/or its affiliates.
# All rights reserved.
# See LICENSE file in this distribution.
# SPDX-License-Identifier: Apache-2.0

"""
These classes define data structures and request/response formats for
IoT applications, particularly for Bluetooth Low Energy (BLE)
communication.
"""
from typing import List
from enum import Enum
from .zigbee import DataParameter
from .common import *
from .scim import Device
from dataclasses import dataclass


class BleReadRequest:
    """
    Represents a request for reading data from a BLE device.
    It includes service_uuid and characteristic_uuid.
    """
    service_uuid: str = ""
    characteristic_uuid: str = ""

    def __init__(self, service_uuid: str, characteristic_uuid: str):
        self.service_uuid = service_uuid
        self.characteristic_uuid = characteristic_uuid


    def __json__(self):
        return self.__dict__()
    

    def __dict__(self):
        return {
            "serviceUUID": self.service_uuid,
            "characteristicUUID": self.characteristic_uuid
        }


class BleSubscribeRequest:
    """
    Represents a request for subscribing to data from a BLE device. It includes serviceUUID and characteristicUUID.
    """
    def __init__(self, serviceUUID: str, characteristicUUID: str):
        self.serviceUUID = serviceUUID
        self.characteristicUUID = characteristicUUID


    def __json__(self):
        return self.__dict__()


    def __dict__(self):
        return {
            "serviceUUID": self.serviceUUID,
            "characteristicUUID": self.characteristicUUID
        }


class BleConnectRequest:
    """ 
    Represents a request for establishing a connection with BLE devices.
    It includes a list of services, the number of retries, and a flag for
    retryMultipleAPs. 
    """
    def __init__(self, services: List[str], retries: int, retryMultipleAPs: bool):
        self.services = services
        self.retries = retries
        self.retryMultipleAPs = retryMultipleAPs


    def __json__(self):
        return self.__dict__()


    def __dict__(self):
        return {
            "services": [
            {
                "serviceID": service
            } for service in self.services
            ],
            "retries": self.retries,
            "retryMultipleAPs": self.retryMultipleAPs
        }

class BleDataParameter(DataParameter):
    """
    Represents parameters for BLE data, including device_id, serviceUUID,
    charUUID, and optional flags.
    """
    def __init__(self, device_id, serviceUUID, charUUID, flags=None):
        super().__init__(device_id)
        self.serviceUUID = serviceUUID
        self.charUUID = charUUID
        self.flags = flags if flags else []


    def __json__(self):
        return self.__dict__()


    def __dict__(self):
        return {
            "deviceId": self.device_id,
            "serviceUUID": self.serviceUUID,
            "charUUID": self.charUUID,
            "flags": self.flags
        }


class BleWriteRequest:
    """ 
    Represents a request for writing data to a BLE device. 
    It includes service_uuid, characteristic_uuid, and value. 
    """
    def __init__(self, service_uuid, characteristic_uuid, value):
        self.service_uuid = service_uuid
        self.characteristic_uuid = characteristic_uuid
        self.value = value


    def __json__(self):
        return self.__dict__()


    def __dict__(self):
        return {
            "serviceUUID": self.service_uuid,
            "characteristicUUID": self.characteristic_uuid,
            "value": self.value
        }


class BleDiscoverResponse:
    """
    Represents a response containing information about BLE services
    and characteristics. It includes a list of services.
    """
    def __init__(self, services: List = []):
        self.services = services


    def toParameterList(self, device_id: str) -> List[DataParameter]:
        """ function toParameterList """
        parameters = []
        for service in self.services:
            for characteristic in service.get('characteristics'):
                parameter = BleDataParameter(device_id, service.get('uuid'), characteristic.get('uuid'), characteristic.get('flags'))
                parameters.append(parameter)
        return parameters


    class BleService:
        """ class BLE Service """
        def __init__(self):
            self.uuid = ""
            self.characteristics = []


    class BleCharacteristic:
        """ BLE Characteristic Class """
        def __init__(self):
            self.uuid = ""
            self.flags = []
            self.descriptors = []


    class BleDescriptors:
        """ BLE Descriptor Class """
        def __init__(self):
            self.uuid = ""


    def __json__(self):
        return self.__dict__()


    def __dict__(self):
        return {
            "services": self.services
        }
    

class BleAdvertisementFilterType(Enum):
    """
    An enumeration of BLE advertisement filter types, including
    ALLOW and DENY.
    """
    ALLOW = "allow"
    DENY = "deny"


    def __json__(self):
        return self.value
   
   
    def __dict__(self):
        return self.value


class BleAdvertisementFilter:
    """
    Represents a filter for BLE advertisements, including mac,
    adType, and adData.
    """
    mac: str
    adType: str
    adData: str


class BleUnsubscribeRequest:
    """
    Represents a request for unsubscribing from BLE data. It includes
    serviceUUID and characteristicUUID.
    """
    def __init__(self, serviceUUID: str, characteristicUUID: str):
        self.serviceUUID = serviceUUID
        self.characteristicUUID = characteristicUUID


    def __json__(self):
        return self.__dict__()


    def __dict__(self):
        return {
            "serviceUUID": self.serviceUUID,
            "characteristicUUID": self.characteristicUUID
        }


class BleTopicType(Enum):
    """
    An enumeration of BLE topic types, including GATT, ADVERTISEMENTS,
    and CONNECTION.
    """
    GATT = 'gatt'
    ADVERTISEMENTS = 'advertisements'
    CONNECTION = 'connection'

    def __json__(self):
        return self.__dict__()


    def __dict__(self):
        return self.value
    

class BleRegisterTopicRequest:
    """
    Represents a request for registering a BLE topic. It includes
    the topic type.
    """
    type: BleTopicType

    def __init__(self, type):
        super().__init__()
        self.type = type


    def __json__(self):
        return self.__dict__()


    def __dict__(self):
        return {
            "type": self.type
        }


class BleGattTopic(BleRegisterTopicRequest):
    """
    Represents a specific GATT topic for BLE. It includes serviceUUID
    and characteristicUUID.
    """
    serviceUUID: str
    characteristicUUID: str

    def __init__(self, serviceUUID: str, characteristicUUID: str):
        super().__init__(type=BleTopicType.GATT)
        self.serviceUUID = serviceUUID
        self.characteristicUUID = characteristicUUID


    def __json__(self):
        return self.__dict__()


    def __dict__(self):
        parent_dict = super().__dict__()
        current_dict = {
            "serviceUUID": self.serviceUUID,
            "characteristicUUID": self.characteristicUUID
        }
        return {**parent_dict, **current_dict}


class BleAdvertisementTopic(BleRegisterTopicRequest):
    """
    Represents a topic for BLE advertisements. It includes filterType
    and filters.
    """
    filterType: str
    filters: List

    def __init__(self, filterType: str, filters: List):
        super().__init__(type=BleTopicType.ADVERTISEMENTS)
        self.filterType = filterType
        self.filters = filters


    def __json__(self):
        return self.__dict__()


    def __dict__(self):
        parent_dict = super().__dict__()
        current_dict = {
            "filterType": self.filterType,
            "filters": self.filters
        }
        return {**parent_dict, **current_dict}


class BleConnectionTopic(BleRegisterTopicRequest):
    """ Represents a topic for BLE connection-related data. """
    def __init__(self):
        super().__init__(type=BleTopicType.CONNECTION)


    def __json__(self):
        return self.__dict__()


    def __dict__(self):
        return super().__dict__()
    

@dataclass
class DataParameter:
    """
    Unique ID of the device
    """
    device_id: str

    def __json__(self):
        return self.__dict__()


    def __dict__(self):
        return {
            "device_id": self.device_id
        }


@dataclass
class RegistrationOptions:
    """
    data class for specifying data registration options. It includes
    a list of devices and the data format.
    """
    devices: List[Device]
    devices: List[Device]
    dataFormat: DataFormat

    def __json__(self):
        return self.__dict__()
    

    def __dict__(self):
        return {
            "devices": self.devices,
            "dataFormat": self.dataFormat
        }


@dataclass
class DataRegistrationOptions(RegistrationOptions):
    """
    data class that extends RegistrationOptions and includes a
    dataParameter field for more specific data registration.
    """
    dataParameter: DataParameter

    def __json__(self):
        return self.__dict__()


    def __dict__(self):
        return {
            "devices": self.devices,
            "dataFormat": self.dataFormat,
            "dataParameter": self.dataParameter
        }


@dataclass
class ConnectionRegistrationOptions(RegistrationOptions):
    pass


@dataclass
class AdvertisementRegistrationOptions(RegistrationOptions):
    """  Management of Advertisement Registration Options """
    advertisementFilterType: BleAdvertisementFilterType
    advertisementFilters: List[BleAdvertisementFilter]

    def __json__(self):
        return self.__dict__()


    def __dict__(self):
        return {
            "devices": self.devices,
            "dataFormat": self.dataFormat,
            "advertisementFilterType": self.advertisementFilterType,
            "advertisementFilters": self.advertisementFilters
        }
