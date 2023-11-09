#!python
# Copyright (c) 2023, Cisco Systems, Inc. and/or its affiliates.
# All rights reserved.
# See LICENSE file in this distribution.
# SPDX-License-Identifier: Apache-2.0

"""

Classes for IoT technology, data formats, parameters, list responses, 
and subscription options used in IoT applications.

"""

from enum import Enum
from typing import Generic, List, Optional, TypeVar

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class Technology(Enum):
    """
    An enumeration class representing IoT technologies, including
    BLE and Zigbee.
    """
    BLE = "ble"
    ZIGBEE = "zigbee"
    DPP = "dpp"
    FIDO_FDO = "fido_fdo"
    LORAWAN = "lorawan"

    def __json__(self):
        return self.value


class DataFormat(Enum):
    """
    An enumeration class representing subscription data formats.
    """
    DEFAULT = "default"
    PAYLOAD = "payload"


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
    start_index: int
    items_per_page: int

    resources: List[Resource] = Field(alias="Resources")


class RegistrationOptions(BaseModel):
    """
    A class representing registration options for IoT devices.
    """
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    data_format: Optional[DataFormat] = Field(
        alias="dataFormat", default=DataFormat.DEFAULT)
    data_apps: Optional[List[str]] = Field(alias="dataApps", default=None)


class DataRegistrationOptions(RegistrationOptions):
    """
    A class representing registration options for IoT devices.
    """

    data_parameter: Optional[DataParameter] = Field(
        alias="dataParameter", default=None)


class ConnectionRegistrationOptions(RegistrationOptions):
    """ A class representing registration options for BLE devices. """


class DataApp(BaseModel):
    """ A class representing a data app. """
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    data_app_id: str = Field(alias="dataAppID")
