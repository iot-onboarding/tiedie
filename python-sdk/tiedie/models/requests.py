#!python
# Copyright (c) 2023, Cisco Systems, Inc. and/or its affiliates.
# All rights reserved.
# See LICENSE file in this distribution.
# SPDX-License-Identifier: Apache-2.0

"""
These classes are designed for structured communication with the
Tiedie IoT platform.  They enable the creation of requests for
reading, subscribing, writing, and managing topics for IoT devices
using BLE and Zigbee technologies.
"""

from typing import List, Optional

from pydantic import Base64Bytes, BaseModel, ConfigDict, Field, computed_field
from pydantic.alias_generators import to_camel
from tiedie.models.ble import (AdvertisementRegistrationOptions,
                               BleAdvertisementTopic,
                               BleConnectRequest,
                               BleConnectionTopic,
                               BleDataParameter,
                               BleGattTopic,
                               BleReadRequest, BleTopicType)
from tiedie.models.common import (ConnectionRegistrationOptions, DataApp,
                                  DataFormat,
                                  DataParameter,
                                  DataRegistrationOptions,
                                  RegistrationOptions,
                                  Technology)

from tiedie.models.scim import Device
from tiedie.models.zigbee import ZigbeeDataParameter, ZigbeeReadRequest, ZigbeeRegisterTopicRequest


class TiedieReadRequest(BaseModel):
    """
    A request for reading data from IoT devices, with support for both
    BLE and Zigbee technologies. 
    """
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    data_parameter: DataParameter = Field(exclude=True)

    @computed_field
    @property
    def ble(self) -> Optional[BleReadRequest]:
        """ Returns the BLE read request. """
        if self.technology == Technology.BLE and \
                isinstance(self.data_parameter, BleDataParameter):
            return BleReadRequest(
                service_id=self.data_parameter.service_id,  # pylint: disable=no-member
                characteristic_id=self.data_parameter.characteristic_id  # pylint: disable=no-member
            )

        return None

    @computed_field
    @property
    def zigbee(self) -> Optional[ZigbeeReadRequest]:
        """ Returns the Zigbee read request. """
        if self.technology == Technology.ZIGBEE and \
                isinstance(self.data_parameter, ZigbeeDataParameter):
            return ZigbeeReadRequest(
                endpoint_id=self.data_parameter.endpoint_id,  # pylint: disable=no-member
                cluster_id=self.data_parameter.cluster_id,  # pylint: disable=no-member
                attribute_id=self.data_parameter.attribute_id,  # pylint: disable=no-member
                type=self.data_parameter.attribute_type  # pylint: disable=no-member
            )

        return None


class TiedieWriteRequest(TiedieReadRequest):
    """
    A request class for writing data to IoT devices, supporting both
    BLE and Zigbee technologies.
    """

    value: str

class BleConnectProtocolMap(BaseModel):
    """ Object with BLE connect protocol map """
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    ble: BleConnectRequest

class TiedieConnectRequest(BaseModel):
    """
    A request class for establishing a connection with BLE devices,
    primarily used for BLE technology.
    """
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    protocol_map: BleConnectProtocolMap
    retries: Optional[int] = 3
    retry_multiple_aps: Optional[bool] = Field(alias=str("retryMultipleAPs"), default=True)

class BlePropertyProtocolMap(BaseModel):
    """ Object with BLE property protocol map """
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    service_id: str = Field(alias=str("serviceID"))
    characteristic_id: str = Field(alias=str("characteristicID"))

class PropertyProtocolMap(BaseModel):
    """ Object with protocol map for property """
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    ble: BlePropertyProtocolMap

class SdfProperty(BaseModel):
    """ Object with SDF property """
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    description: Optional[str] = None
    observable: Optional[bool] = True
    readable: Optional[bool] = True
    writable: Optional[bool] = True
    protocol_map: PropertyProtocolMap

class GattEventProtocolMap(BaseModel):
    """ Object with GATT event protocol map """
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    type: str = Field(alias=str("type"), default=BleTopicType.GATT)
    service_id: str = Field(alias=str("serviceID"))
    characteristic_id: str = Field(alias=str("characteristicID"))

class AdvertisementEventProtocolMap(BaseModel):
    """ Object with advertisement event protocol map """
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    type: str = Field(alias=str("type"), default=BleTopicType.ADVERTISEMENTS)

class ConnectionEventProtocolMap(BaseModel):
    """ Object with connection event protocol map """
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    type: str = Field(alias=str("type"), default=BleTopicType.CONNECTION_EVENTS)


class EventProtocolMap(BaseModel):
    """ Object with event protocol map """
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    ble: GattEventProtocolMap | AdvertisementEventProtocolMap | ConnectionEventProtocolMap

class SdfOutputData(BaseModel):
    """ Object with SDF output data """
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    type: Optional[str] = None
    protocol_map: EventProtocolMap

class SdfEvent(BaseModel):
    """ Object with SDF event """
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    description: Optional[str] = None
    sdf_output_data: SdfOutputData

class SdfAction(BaseModel):
    """ Object with SDF action """
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    description: Optional[str] = None
    protocol_map: PropertyProtocolMap

class SdfObject(BaseModel):
    """ Object with SDF object """
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    description: Optional[str] = None
    sdf_property: Optional[dict[str, SdfProperty]] = None
    sdf_event: Optional[dict[str, SdfEvent]] = None
    sdf_action: Optional[dict[str, SdfAction]] = None

class SdfThing(SdfObject):
    """ Object with SDF thing """
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    sdf_object: Optional[dict[str, SdfObject]] = None

class SdfModel(BaseModel):
    """ Object with SDF model """
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    namespace: dict[str, str]
    default_namespace: str
    sdf_thing: Optional[dict[str, SdfThing]] = None
    sdf_object: Optional[dict[str, SdfObject]] = None


class PropertyWriteRequest(BaseModel):
    """ Object with property write request """
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    value: Base64Bytes
