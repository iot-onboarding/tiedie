#!python
# Copyright (c) 2023, Cisco and/or its affiliates.
# All rights reserved.
# See LICENSE file in this distribution.
# SPDX-License-Identifier: Apache-2.0

"""
These classes define data structures and request/response formats for
IoT applications, particularly for Bluetooth Low Energy (BLE)
communication.
"""

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

from .common import DataParameter, RegistrationOptions


class BleReadRequest(BaseModel):
    """
    Represents a request for reading data from a BLE device.
    It includes service_uuid and characteristic_uuid.
    """
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    service_id: str = Field(alias="serviceID")
    characteristic_id: str = Field(alias="characteristicID")


class BleSubscribeRequest(BaseModel):
    """
    Represents a request for subscribing to data from a BLE device. 
    It includes serviceUUID and characteristicUUID.
    """
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    service_id: str
    characteristic_id: str


class BleDescriptors(BaseModel):
    """ Represents a BLE descriptor. """
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    descriptor_id: str = Field(alias="descriptorID")


class BleCharacteristic(BaseModel):
    """ Represents a BLE characteristic. """
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    characteristic_id: str = Field(alias="characteristicID")
    flags: List[str]
    descriptors: Optional[List[BleDescriptors]] = None


class BleService(BaseModel):
    """ Represents a BLE service. """
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    service_id: str = Field(alias="serviceID")
    characteristics: Optional[List[BleCharacteristic]] = None


class BleConnectRequest(BaseModel):
    """ 
    Represents a request for establishing a connection with BLE devices.
    It includes a list of services, the number of retries, and a flag for
    retryMultipleAPs. 
    """
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    services: Optional[List[BleService]] = None
    retries: Optional[int] = 3
    retry_multiple_aps: Optional[bool] = Field(alias="retryMultipleAPs", default=True)


class BleDataParameter(DataParameter):
    """
    Represents parameters for BLE data, including device_id, service id,
    characteristic id, and optional flags.
    """

    service_id: str
    characteristic_id: Optional[str] = None
    flags: Optional[List[str]] = None


class BleWriteRequest(BaseModel):
    """ 
    Represents a request for writing data to a BLE device. 
    It includes service_uuid, characteristic_uuid, and value. 
    """
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    service_id: str = Field(alias="serviceID")
    characteristic_id: str = Field(alias="characteristicID")


class BleAdvertisementFilterType(Enum):
    """
    An enumeration of BLE advertisement filter types, including
    ALLOW and DENY.
    """
    ALLOW = "allow"
    DENY = "deny"


class BleAdvertisementFilter(BaseModel):
    """
    Represents a filter for BLE advertisements, including mac,
    adType, and adData.
    """
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    mac: str
    ad_type: str
    ad_data: str


class BleTopicType(Enum):
    """
    An enumeration of BLE topic types, including GATT, ADVERTISEMENTS,
    and CONNECTION_EVENTS.
    """
    GATT = 'gatt'
    ADVERTISEMENTS = 'advertisements'
    CONNECTION_EVENTS = 'connection_events'


class BleRegisterTopicRequest(BaseModel):
    """ A request class for registering topic to BLE devices. """
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    type: BleTopicType = Field(alias="type")


class BleAdvertisementTopic(BleRegisterTopicRequest):
    """
    Represents a topic for BLE advertisements. It includes filterType
    and filters.
    """

    type: BleTopicType = Field(
        alias="type", default=BleTopicType.ADVERTISEMENTS)

    filter_type: Optional[BleAdvertisementFilterType] = Field(
        alias="filterType", default=None)
    filters: Optional[List[BleAdvertisementFilter]] = Field(default=None)


class BleGattTopic(BleRegisterTopicRequest):
    """
    Represents a specific GATT topic for BLE. It includes serviceUUID
    and characteristicUUID.
    """

    type: BleTopicType = Field(alias="type", default=BleTopicType.GATT)
    service_id: str = Field(alias="serviceID")
    characteristic_id: str = Field(alias="characteristicID")


class BleConnectionTopic(BleRegisterTopicRequest):
    """ Represents a topic for BLE connection-related data. """

    type: BleTopicType = Field(
        alias="type", default=BleTopicType.CONNECTION_EVENTS)


class AdvertisementRegistrationOptions(RegistrationOptions):
    """
    A class representing registration options for BLE devices.
    """

    advertisement_filter_type: Optional[BleAdvertisementFilterType] = Field(default=None)
    advertisement_filter: Optional[List[BleAdvertisementFilter]] = Field(default=None)
