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

from pydantic import BaseModel, Field

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
    reason: Optional[str] = None
    error_code: Optional[int] = None

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


class BleDiscoverResponse(TiedieRawResponse):
    """
    Represents a response containing information about BLE services
    and characteristics. It includes a list of services.
    """

    services: list[BleService]

    def to_parameter_list(self, device_id: str) -> List[BleDataParameter]:
        """ Create a generic parameter list from the services and characteristics. """
        parameter_list: List[BleDataParameter] = []

        for service in self.services:
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

class MultiConnectionsResponse(TiedieRawResponse):
    """ Represents a response for connections from multiple BLE devices. """

    connections: List[TiedieDeviceResponse]
