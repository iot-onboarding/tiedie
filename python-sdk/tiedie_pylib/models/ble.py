#!python
# Copyright (c) 2023, Cisco Systems, Inc. and/or its affiliates.
# All rights reserved.
# See accompanying LICENSE file in this distribution.

from typing import List
from enum import Enum
from .zigbee import DataParameter
from .common import *
from .scim import Device
from dataclasses import dataclass


class BleReadRequest:
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
    def __init__(self, services: List = []):
        self.services = services


    def toParameterList(self, device_id: str) -> List[DataParameter]:
        parameters = []
        for service in self.services:
            for characteristic in service.get('characteristics'):
                parameter = BleDataParameter(device_id, service.get('uuid'), characteristic.get('uuid'), characteristic.get('flags'))
                parameters.append(parameter)
        return parameters


    class BleService:
        def __init__(self):
            self.uuid = ""
            self.characteristics = []


    class BleCharacteristic:
        def __init__(self):
            self.uuid = ""
            self.flags = []
            self.descriptors = []


    class BleDescriptors:
        def __init__(self):
            self.uuid = ""


    def __json__(self):
        return self.__dict__()


    def __dict__(self):
        return {
            "services": self.services
        }
    

class BleAdvertisementFilterType(Enum):
    ALLOW = "allow"
    DENY = "deny"


    def __json__(self):
        return self.value
   
   
    def __dict__(self):
        return self.value


class BleAdvertisementFilter:
    mac: str
    adType: str
    adData: str


class BleUnsubscribeRequest:
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
    GATT = 'gatt'
    ADVERTISEMENTS = 'advertisements'
    CONNECTION = 'connection'

    def __json__(self):
        return self.__dict__()


    def __dict__(self):
        return self.value
    

class BleRegisterTopicRequest:
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
