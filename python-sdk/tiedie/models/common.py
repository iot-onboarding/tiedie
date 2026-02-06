# Copyright (c) 2023, Cisco Systems, Inc. and/or its affiliates.
# All rights reserved.
# See LICENSE file in this distribution.
# SPDX-License-Identifier: Apache-2.0

"""

Classes for IoT parameters, list responses, and subscription options used in IoT applications.

"""

from enum import IntEnum
from typing import Generic, List, Optional, TypeVar

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class NipcErrorCodes(IntEnum):
    """
    Error codes as defined in the NIPC draft.
    """
    # Base error codes
    GENERIC_ERROR = 1000
    APP_NOT_AUTHORIZED = 1001
    INVALID_DEVICE_ID = 1002
    INVALID_SDF_URL = 1003
    PREVIOUS_OPERATION_FAILED = 1004

    # Property error codes
    PROPERTY_NOT_READABLE = 1100
    PROPERTY_NOT_WRITABLE = 1101

    # Event error codes
    EVENT_ALREADY_ENABLED = 1200
    EVENT_NOT_ENABLED = 1201
    EVENT_NOT_REGISTERED = 1202

    # Connection error codes
    DEVICE_ALREADY_CONNECTED = 1300
    NO_CONNECTION_FOUND = 1301
    BLE_CONNECTION_TIMEOUT = 1302
    BLE_BONDING_FAILED = 1303
    BLE_CONNECTION_FAILED = 1304
    BLE_SERVICE_DISCOVERY_FAILED = 1305
    INVALID_BLE_SERVICE_OR_CHARACTERISTIC = 1306
    ZIGBEE_CONNECTION_TIMEOUT = 1400
    INVALID_ZIGBEE_ENDPOINT_OR_CLUSTER = 1401

    # Broadcast error codes
    INVALID_BROADCAST_DATA = 1500


class DataParameter(BaseModel):
    """ A class for storing data parameters, with a device_id attribute. """

    device_id: Optional[str] = None


Resource = TypeVar("Resource", bound=BaseModel)


class ListResponse(BaseModel, Generic[Resource]):
    """
    A class representing a list response with attributes for totalResults,
    startIndex, itemsPerPage, and resources.
    """
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    total_results: int
    start_index: Optional[int] = None
    items_per_page: Optional[int] = None

    resources: Optional[List[Resource]] = Field(alias=str("Resources"), default=[])


class RegistrationOptions(BaseModel):
    """
    A class representing registration options for IoT devices.
    """
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    data_apps: Optional[List[str]] = Field(alias=str("dataApps"), default=None)


class DataRegistrationOptions(RegistrationOptions):
    """
    A class representing registration options for IoT devices.
    """

    data_parameter: Optional[DataParameter] = Field(
        alias=str("dataParameter"), default=None)


class ConnectionRegistrationOptions(RegistrationOptions):
    """ A class representing registration options for BLE devices. """


class DataApp(BaseModel):
    """ A class representing a data app. """
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    data_app_id: str = Field(alias=str("dataAppID"))
