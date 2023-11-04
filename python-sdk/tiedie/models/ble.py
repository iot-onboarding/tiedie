#!python
# Copyright (c) 2023, Cisco Systems, Inc. and/or its affiliates.
# All rights reserved.
# See LICENSE file in this distribution.
# SPDX-License-Identifier: Apache-2.0

from typing import List
from enum import Enum
from .zigbee import DataParameter
from .common import *
from .scim import Device
from dataclasses import dataclass


@dataclass
class DataParameter:
    device_id: str


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
            "flags": self.flags if self.flags else []
        }
    

class BleServicesRequest:
    def __init__(self, services: List[str]):
        self.services = services


    def __json__(self):
        return self.__dict__()


    def __dict__(self):
        return {
            "services": [
            {
                "serviceID": service
            } for service in self.services
            ]
        }
    

class BleDiscoveServices:
    def __init__(self, services: List = []):
        self.services = services


    def toParameterList(self, device_id: str):
        parameters = []
        for service in self.services:
            for characteristic in service.get('characteristics'):
                parameter = BleDataParameter(device_id, service.get('serviceUUID'), characteristic.get('characteristicUUID'), characteristic.get('flags'))
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
    

class BleReadWriteRequest:
    def __init__(self, service_uuid: str = "", characteristic_uuid: str = ""):
        self.service_uuid = service_uuid
        self.characteristic_uuid = characteristic_uuid


    def __json__(self):
        return self.__dict__()
    

    def __dict__(self):
        return {
            "serviceID": self.service_uuid,
            "characteristicID": self.characteristic_uuid
        }


class BleSubscribeRequest:
    def __init__(self, serviceUUID: str, characteristicUUID: str):
        self.serviceUUID = serviceUUID
        self.characteristicUUID = characteristicUUID


    def __json__(self):
        return self.__dict__()


    def __dict__(self):
        return {
            "serviceID": self.serviceUUID,
            "characteristicID": self.characteristicUUID
        }


class BleUnsubscribeRequest:
    def __init__(self, serviceUUID: str, characteristicUUID: str):
        self.serviceUUID = serviceUUID
        self.characteristicUUID = characteristicUUID


    def __json__(self):
        return self.__dict__()


    def __dict__(self):
        return {
            "serviceID": self.serviceUUID,
            "characteristicID": self.characteristicUUID
        }


class BleAdvertisementFilter:
    mac: str
    adType: str
    adData: str


class BleAdvertisementFilterType(Enum):
    ALLOW = "allow"
    DENY = "deny"


    def __json__(self):
        return self.value
   
   
    def __dict__(self):
        return self.value
    

class BleRegisterTopicRequest:
    type: BLETopicType

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
    def __init__(self, data_parameter: BleDataParameter):
        super().__init__(type=BLETopicType.GATT)
        self.data_parameter = data_parameter

    def __json__(self):
        return self.__dict__()


    def __dict__(self):
        parent_dict = super().__dict__()
        current_dict = {
            "serviceID": self.data_parameter.serviceUUID,
            "characteristicID": self.data_parameter.charUUID
        }
        return {**parent_dict, **current_dict}


class BleAdvertisementTopic(BleRegisterTopicRequest):
    filterType: str
    filters: List

    def __init__(self, filterType: str, filters: List):
        super().__init__(type=BLETopicType.ADV)
        self.filterType = filterType
        self.filters = filters


    def __json__(self):
        return self.__dict__()


    def __dict__(self):
        parent_dict = super().__dict__()
        current_dict = {
            "filterType": self.filterType,
            "filters": self.filters if self.filters else []
        }
        return {**parent_dict, **current_dict}


class BleConnectionTopic(BleRegisterTopicRequest):
    def __init__(self):
        super().__init__(type=BLETopicType.CONN)


    def __json__(self):
        return self.__dict__()


    def __dict__(self):
        return super().__dict__()
    

@dataclass
class RegistrationOptions:
    type: BLETopicType = None
    dataFormat: RegisterDataFormat = None


@dataclass
class DataRegistrationOptions(RegistrationOptions):
    def __init__(self, service: BleDataParameter, dataformat: RegisterDataFormat = None):
        super().__init__(BLETopicType.GATT, dataformat)
        self.service = service


@dataclass
class ConnectionRegistrationOptions(RegistrationOptions):
    def __init__(self, dataformat: RegisterDataFormat = None, deviceID: str = None):
        super().__init__(BLETopicType.CONN, dataformat)
        self.dataformat = dataformat
        self.deviceID = deviceID


@dataclass
class AdvertisementRegistrationOptions(RegistrationOptions):
    def __init__(self, filterType: BleAdvertisementFilterType = None, filters: List[BleAdvertisementFilter] = None, 
                 dataformat: RegisterDataFormat = None, deviceID = None):
        super().__init__(BLETopicType.ADV, dataformat)
        self.deviceID = deviceID
        self.filterType = filterType
        self.filters = filters