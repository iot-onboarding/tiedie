#!python

# Copyright (c) 2023, Cisco Systems, Inc. and/or its affiliates.
# All rights reserved.
# See LICENSE file in this distribution.
# SPDX-License-Identifier: Apache-2.0

"""

This Python module manages Tiedie IoT platform responses and requests, 
including handling Tiedie responses, data responses, and discovery-related inteactions.

"""

from dataclasses import dataclass
from enum import Enum
from typing import Generic, List, Optional, TypeVar
from pydantic.alias_generators import to_camel

from pydantic import Base64Bytes, BaseModel, ConfigDict, Field

from tiedie.models.ble import BleDataParameter, BleService


class TiedieStatus(Enum):
    """ TieDie Status """
    FAILURE = "FAILURE"
    SUCCESS = "SUCCESS"


T_co = TypeVar('T_co', covariant=True)


class TiedieHTTP(BaseModel):
    """ TieDie HTTP """
    status_code: int
    status_message: str


class TiedieRawResponse(BaseModel):
    """ Raw representation of the TieDie response """

    status: Optional[TiedieStatus] = None
    detail: Optional[str] = None
    nipc_status: Optional[int] = None

    http: Optional[TiedieHTTP] = None


class TiedieResponse(TiedieRawResponse, Generic[T_co]):
    """ TieDie response """
    body: Optional[T_co] = None


@dataclass
class HttpResponse(Generic[T_co]):
    """ class HttpResponse """

    status_code: int
    message: str
    body: T_co


class ValueResponse(TiedieRawResponse):
    """ Class for data response with value and status. """

    value: Optional[str] = None

class BleServiceProtocolMap(BaseModel):
    """ Represents a map of BLE service protocol. """

    ble: list[BleService]

class BleDiscoverResponse(TiedieRawResponse):
    """
    Represents a response containing information about BLE services
    and characteristics. It includes a list of services.
    """

    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    protocol_map: BleServiceProtocolMap

    def to_parameter_list(self, device_id: str) -> List[BleDataParameter]:
        """ Create a generic parameter list from the services and characteristics. """
        parameter_list: List[BleDataParameter] = []

        for service in self.protocol_map.ble:
            if service.characteristics is None:
                continue
            for characteristic in service.characteristics:
                parameter_list.append(BleDataParameter(
                    device_id=device_id,
                    service_id=service.service_id,
                    characteristic_id=characteristic.characteristic_id,
                    flags=characteristic.flags
                ))

        return parameter_list

class TiedieDeviceResponse(TiedieRawResponse):
    """ Represents a response for a single BLE device. """

    device_id: Optional[str] = Field(alias=str("id"))

class PropertyResponse(TiedieRawResponse):
    """ Represents a response for a property. """

    device_id: str = Field(alias=str("id"))
    property: str = Field(alias=str("property"))
    value: Base64Bytes

class ActionResponse(TiedieRawResponse):
    """ Represents a response for an action. """

    device_id: str = Field(alias=str("id"))
    action: str = Field(alias=str("action"))
    value: Base64Bytes

class MultiConnectionsResponse(TiedieRawResponse):
    """ Represents a response for connections from multiple BLE devices. """

    connections: List[TiedieDeviceResponse]

class ModelRegistrationResponse(TiedieRawResponse):
    """ Represents a response for SDF model registration. """

    sdf_name: str = Field(alias=str("sdfName"))

class Event(BaseModel):
    """ Represents an event in the data app registration response. """

    event: str

class MqttBrokerConfig(BaseModel):
    """ Represents the MQTT broker configuration. """
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    uri: str = Field(alias=str("URI"))
    username: str
    password: str
    broker_ca_cert: Optional[str] = Field(alias=str("brokerCACert"), default=None)
    custom_topic: Optional[str] = Field(alias=str("customTopic"), default=None)

class DataAppRegistration(TiedieRawResponse):
    """ Represents a response for data app registration. """
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    events: List[Event]

    mqtt_client: Optional[dict] = None
    mqtt_broker: Optional[MqttBrokerConfig]

class TiedieEventResponse(TiedieRawResponse):
    """ Represents a response for an event. """

    event: str
    device_id: str = Field(alias=str("id"))

class TiedieEventsResponse(TiedieRawResponse):
    """ Represents a response for multiple events. """

    events: List[TiedieEventResponse]
