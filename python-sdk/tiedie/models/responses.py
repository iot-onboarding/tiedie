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


class NipcProblemTypes(str, Enum):
    """
    NIPC Problem Details error types as defined in the NIPC draft
    (https://datatracker.ietf.org/doc/html/draft-ietf-asdf-nipc-09)
    Section 6 and IANA registry Section 10.4.
    """
    # Base URI for IANA HTTP Problem Types registry
    _IANA_BASE = "https://www.iana.org/assignments/nipc-problem-types#"

    # Generic errors
    INVALID_ID = _IANA_BASE + "invalid-id"
    INVALID_SDF_URL = _IANA_BASE + "invalid-sdf-url"
    EXTENSION_OPERATION_NOT_EXECUTED = _IANA_BASE + "extension-operation-not-executed"
    SDF_MODEL_ALREADY_REGISTERED = _IANA_BASE + "sdf-model-already-registered"
    SDF_MODEL_IN_USE = _IANA_BASE + "sdf-model-in-use"

    # Property API errors
    PROPERTY_NOT_READABLE = _IANA_BASE + "property-not-readable"
    PROPERTY_NOT_WRITABLE = _IANA_BASE + "property-not-writable"

    # Event API errors
    EVENT_ALREADY_ENABLED = _IANA_BASE + "event-already-enabled"
    EVENT_NOT_ENABLED = _IANA_BASE + "event-not-enabled"
    EVENT_NOT_REGISTERED = _IANA_BASE + "event-not-registered"

    # Protocol specific errors - BLE
    PROTOCOLMAP_BLE_ALREADY_CONNECTED = _IANA_BASE + "protocolmap-ble-already-connected"
    PROTOCOLMAP_BLE_NO_CONNECTION = _IANA_BASE + "protocolmap-ble-no-connection"
    PROTOCOLMAP_BLE_CONNECTION_TIMEOUT = _IANA_BASE + "protocolmap-ble-connection-timeout"
    PROTOCOLMAP_BLE_BONDING_FAILED = _IANA_BASE + "protocolmap-ble-bonding-failed"
    PROTOCOLMAP_BLE_CONNECTION_FAILED = _IANA_BASE + "protocolmap-ble-connection-failed"
    PROTOCOLMAP_BLE_SERVICE_DISCOVERY_FAILED = _IANA_BASE + \
        "protocolmap-ble-service-discovery-failed"
    PROTOCOLMAP_BLE_INVALID_SERVICE_OR_CHARACTERISTIC = _IANA_BASE + \
        "protocolmap-ble-invalid-service-or-characteristic"

    # Protocol specific errors - Zigbee
    PROTOCOLMAP_ZIGBEE_CONNECTION_TIMEOUT = \
        _IANA_BASE + "protocolmap-zigbee-connection-timeout"
    PROTOCOLMAP_ZIGBEE_INVALID_ENDPOINT_OR_CLUSTER = \
        _IANA_BASE + "protocolmap-zigbee-invalid-endpoint-or-cluster"

    # Extension API errors
    EXTENSION_BROADCAST_INVALID_DATA = _IANA_BASE + "extension-broadcast-invalid-data"
    EXTENSION_FIRMWARE_ROLLBACK = _IANA_BASE + "extension-firmware-rollback"
    EXTENSION_FIRMWARE_UPDATE_FAILED = _IANA_BASE + "extension-firmware-update-failed"

    # RFC 9457 generic error for internal server errors
    ABOUT_BLANK = "about:blank"


class ProblemDetails(BaseModel):
    """RFC 9457 Problem Details for HTTP APIs.

    Used for error responses with application/problem+json content type.
    """
    model_config = ConfigDict(populate_by_name=True)

    type: NipcProblemTypes = Field(..., description="URI identifying the problem type")
    status: int = Field(..., description="HTTP status code")
    title: str = Field(..., description="Human-readable summary of the problem type")
    detail: Optional[str] = Field(None, description="Human-readable explanation of this occurrence")


class SuccessResponse(BaseModel):
    """Base class for successful NIPC responses.

    Success responses return HTTP 200 with specific response schemas.
    """


T_co = TypeVar('T_co', covariant=True)


class TiedieHTTP(BaseModel):
    """ TieDie HTTP """
    status_code: int
    status_message: str
    headers: Optional[dict[str, str]] = None


class NipcResponse(BaseModel, Generic[T_co]):
    """NIPC API Response that can contain either success data or error details.

    Follows the new NIPC specification with proper HTTP status handling.
    For errors, contains ProblemDetails. For success, contains the response body.
    """
    # HTTP metadata
    http: Optional[TiedieHTTP] = None

    # Response body for successful requests (HTTP 200)
    body: Optional[T_co] = None

    # Error details for failed requests (HTTP 4xx/5xx)
    error: Optional[ProblemDetails] = None

    @property
    def is_success(self) -> bool:
        """Returns True if the response indicates success."""
        return self.error is None and (self.http is None or self.http.status_code < 400)

    @property
    def is_error(self) -> bool:
        """Returns True if the response indicates an error."""
        return self.error is not None or (self.http is not None and self.http.status_code >= 400)


@dataclass
class HttpResponse(Generic[T_co]):
    """ class HttpResponse """

    status_code: int
    message: str
    body: T_co


class ValueResponse(SuccessResponse):
    """ Class for data response with value and status. """

    value: Optional[str] = None

class BleServiceProtocolMap(BaseModel):
    """ Represents a map of BLE service protocol. """

    ble: list[BleService]

class BleDiscoverResponse(SuccessResponse):
    """
    Represents a response containing information about BLE services
    and characteristics. It includes a list of services.
    """

    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    sdf_protocol_map: BleServiceProtocolMap

    def to_parameter_list(self, device_id: str) -> List[BleDataParameter]:
        """ Create a generic parameter list from the services and characteristics. """
        parameter_list: List[BleDataParameter] = []

        for service in self.sdf_protocol_map.ble:
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

class TiedieDeviceResponse(SuccessResponse):
    """ Represents a response for a single BLE device. """

    device_id: Optional[str] = Field(alias=str("id"))

class PropertyResponse(SuccessResponse):
    """ Represents a response for a property. """

    property: str = Field(alias=str("property"))
    value: Base64Bytes

class PropertyWriteResponse(SuccessResponse):
    """ Represents a response for a property write. """

    status: int

class ActionResponse(SuccessResponse):
    """ Represents a response for an action. """

    action: str = Field(alias=str("action"))
    value: Base64Bytes

class MultiConnectionsResponse(SuccessResponse):
    """ Represents a response for connections from multiple BLE devices. """

    connections: List[TiedieDeviceResponse]

class ModelRegistrationResponse(SuccessResponse):
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

class DataAppRegistration(SuccessResponse):
    """ Represents a response for data app registration. """
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    events: List[Event]

    mqtt_client: Optional[bool] = False
    mqtt_broker: Optional[MqttBrokerConfig] = None

class TiedieEventResponse(SuccessResponse):
    """ Represents a response for an event. """

    event: str
    instance_id: str = Field(alias=str("instanceId"))
