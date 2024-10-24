#!python
# Copyright (c) 2023, Cisco Systems, Inc. and/or its affiliates.
# All rights reserved.
# See LICENSE file in this distribution.
# SPDX-License-Identifier: Apache-2.0

"""
This Python module defines classes for managing device information
with extensions for BLE and endpoint applications.  It also provides
methods for serialization and deserialization from JSON.
"""

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, computed_field
from pydantic.alias_generators import to_camel


class NullPairing(BaseModel):
    """ Represents Null Pairing with an ID. """


class PairingJustWorks(BaseModel):
    """ class PairingJustWorks """
    key: Optional[int] = None


class PairingPassKey(BaseModel):
    """ Represents Pairing with Pass Key."""
    key: int


class PairingOOB(BaseModel):
    """ Represents Out-of-Band Pairing with keys and numbers. """
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    key: str
    random_number: str
    confirmation_number: Optional[str] = None


class BleExtension(BaseModel):
    """ Contains BLE extension data and initialization method. """
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    version_support: List[str]
    device_mac_address: str
    is_random: bool = False
    irk: Optional[str] = None
    mobility: bool = False
    null_pairing: Optional[NullPairing] = Field(
        alias=str("urn:ietf:params:scim:schemas:extension:pairingNull:2.0:Device"),
        default=None)
    pairing_just_works: Optional[PairingJustWorks] = Field(
        alias=str("urn:ietf:params:scim:schemas:extension:pairingJustWorks:2.0:Device"),
        default=None)
    pairing_pass_key: Optional[PairingPassKey] = Field(
        alias=str("urn:ietf:params:scim:schemas:extension:pairingPassKey:2.0:Device"),
        default=None)
    pairing_oob: Optional[PairingOOB] = Field(
        alias=str("urn:ietf:params:scim:schemas:extension:pairingOOB:2.0:Device"),
        default=None)

    @computed_field(alias=str("pairingMethods"))
    @property
    def pairing_methods(self) -> List[str]:
        """ Returns a list of pairing methods.

        Returns:
            List[str]: List of pairing methods.
        """

        _pairing_methods = []
        if self.null_pairing:
            _pairing_methods.append(
                "urn:ietf:params:scim:schemas:extension:pairingNull:2.0:Device")
        if self.pairing_just_works:
            _pairing_methods.append(
                "urn:ietf:params:scim:schemas:extension:pairingJustWorks:2.0:Device")
        if self.pairing_pass_key:
            _pairing_methods.append(
                "urn:ietf:params:scim:schemas:extension:pairingPassKey:2.0:Device")
        if self.pairing_oob:
            _pairing_methods.append(
                "urn:ietf:params:scim:schemas:extension:pairingOOB:2.0:Device")
        return _pairing_methods


class DppExtension(BaseModel):
    """ Represents DPP extension data. """
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    dpp_version: int
    bootstrapping_method: List[str]
    bootstrap_key: str
    device_mac_address: str
    class_channel: List[str]
    serial_number: str


class ZigbeeExtension(BaseModel):
    """ Represents Zigbee extension data. """
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    version_support: List[str]
    device_eui64_address: str


class EndpointAppType(str, Enum):
    """ Represents an endpoint application type. """
    DEVICE_CONTROL = "deviceControl"
    TELEMETRY = "telemetry"


class AppCertificateInfo(BaseModel):
    """ Stores information about an application certificate. """

    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    root_ca: str = Field(alias=str("rootCA"))
    subject_name: str = Field(alias=str("subjectName"))


class EndpointApp(BaseModel):
    """ Stores information about an endpoint application. """
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    application_id: Optional[str] = Field(alias=str("id"), default=None)
    application_type: EndpointAppType
    application_name: str
    client_token: Optional[str] = None
    certificate_info: Optional[AppCertificateInfo] = None


class Application(BaseModel):
    """ Represents an application. """
    value: str
    ref: Optional[str] = Field(alias=str("$ref"), default=None)


class EndpointAppsExtension(BaseModel):
    """ Contains a list of endpoint applications. """
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    applications: List[Application]
    device_control_enterprise_endpoint: Optional[str] = None
    telemetry_enterprise_endpoint: Optional[str] = None


class Device(BaseModel):
    """ Represents a device with extensions and schema handling. """
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    device_id: Optional[str] = Field(alias=str("id"), default=None)
    display_name: str
    active: bool
    ble_extension: Optional[BleExtension] = Field(
        alias=str("urn:ietf:params:scim:schemas:extension:ble:2.0:Device"),
        default=None)
    zigbee_extension: Optional[ZigbeeExtension] = Field(
        alias=str("urn:ietf:params:scim:schemas:extension:zigbee:2.0:Device"),
        default=None)
    dpp_extension: Optional[DppExtension] = Field(
        alias=str("urn:ietf:params:scim:schemas:extension:dpp:2.0:Device"),
        default=None)
    endpoint_apps_extension: Optional[EndpointAppsExtension] = Field(
        alias=str("urn:ietf:params:scim:schemas:extension:endpointAppsExt:2.0:Device"),
        default=None)

    @computed_field
    @property
    def schemas(self) -> List[str]:
        """ schemas property

        Returns:
            List[str]: schemas property
        """
        _schemas = ["urn:ietf:params:scim:schemas:core:2.0:Device"]
        if self.ble_extension is not None:
            _schemas.append(
                "urn:ietf:params:scim:schemas:extension:ble:2.0:Device")
        if self.dpp_extension is not None:
            _schemas.append(
                "urn:ietf:params:scim:schemas:extension:dpp:2.0:Device")
        if self.zigbee_extension is not None:
            _schemas.append(
                "urn:ietf:params:scim:schemas:extension:zigbee:2.0:Device")
        if self.endpoint_apps_extension is not None:
            _schemas.append(
                "urn:ietf:params:scim:schemas:extension:endpointAppsExt:2.0:Device")
        return _schemas
