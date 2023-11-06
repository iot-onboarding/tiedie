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

import json
import uuid
import attr
from typing import List, Optional
from dataclasses import dataclass, field


@dataclass
class NullPairing:
    """ Represents Null Pairing with an ID. """
    id: str


@dataclass
class PairingJustWorks:
    """ class PairingJustWorks """
    key: int


@dataclass
class PairingPassKey:
    """ Represents Pairing with Pass Key."""
    key: int


@dataclass
class PairingOOB:
    """ Represents Out-of-Band Pairing with keys and numbers. """
    key: str
    random_number: str
    confirmation_number: str


@dataclass
class BleExtension:
    """ Contains BLE extension data and initialization method. """
    version_support: List[str] = field(default_factory=list)
    device_mac_address: str = ""
    address_type: bool = False
    pairing_methods: List[str] = field(default_factory=list)
    irk: str = ""
    null_pairing: NullPairing = None
    pairing_just_works: PairingJustWorks = None
    pairing_pass_key: PairingPassKey = None
    pairing_oob: PairingOOB = None


    def __init__(self, device_mac_address: str, version_support: List[str],
                 is_random: bool, pass_key: int):
        self.schemas = \
            ["urn:ietf:params:scim:schemas:extension:ble:2.0:Device"]
        self.device_mac_address = device_mac_address
        self.address_type = "random" if is_random else "public"
        self.version_support = version_support
        self.pairing_pass_key = PairingPassKey(pass_key)

    def __post_init__(self):
        self.versionSupport = self.version_support
        self.deviceMacAddress = self.device_mac_address
        self.addressType = self.address_type
        self.pairingMethods = self.pairing_methods

    def from_dict(cls, data):
        """ extract from dictionary and return an address pointer """
        null_pairing = \
            data.pop("urn:ietf:params:scim:schemas:extension:pairingNull:2.0:Device",
                     None)
        if null_pairing:
            cls.null_pairing = NullPairing(**null_pairing)

        pairing_just_works = \
            data.pop("urn:ietf:params:scim:schemas:extension:pairingJustWorks:2.0:Device",
                     None)
        if pairing_just_works:
            cls.pairing_just_works = PairingJustWorks(**pairing_just_works)

        pairing_pass_key = \
            data.pop("urn:ietf:params:scim:schemas:extension:pairingPassKey:2.0:Device",
                     None)
        if pairing_pass_key:
            cls.pairing_pass_key = PairingPassKey(**pairing_pass_key)

        pairing_oob = \
            data.pop("urn:ietf:params:scim:schemas:extension:pairingOOB:2.0:Device",
                     None)
        if pairing_oob:
            cls.pairing_oob = PairingOOB(**pairing_oob)

        cls.version_support = data.pop("versionSupport", [])
        cls.device_mac_address = data.pop("deviceMacAddress", "")
        cls.address_type = data.pop("isRandom", "")
        cls.pairing_methods = data.pop("pairingMethods", [])

        return cls(**data)

    def to_dict(self):
        """ function to convert to dictionary """
        data = {
            "versionSupport": self.version_support,
            "deviceMacAddress": self.device_mac_address,
            "addressType": self.address_type,
        }
        if self.null_pairing:
            data["urn:ietf:params:scim:schemas:extension:pairingNull:2.0:Device"] \
                = self.null_pairing.__dict__
        if self.pairing_just_works:
            data["urn:ietf:params:scim:schemas:extension:pairingJustWorks:2.0:Device"] \
                = self.pairing_just_works.__dict__
        if self.pairing_pass_key:
            data["urn:ietf:params:scim:schemas:extension:pairingPassKey:2.0:Device"] = \
                self.pairing_pass_key.__dict__
        if self.pairing_oob:
            data["urn:ietf:params:scim:schemas:extension:pairingOOB:2.0:Device"] = \
                self.pairing_oob.__dict__
        return data

    def __json__(self):
        return self.to_dict()

    def __str__(self):
        return str(self.__json__())


@dataclass
class DppExtension:
    """ Represents DPP extension data. """
    dpp_version: int
    bootstrapping_method: List[str]
    bootstrap_key: str
    device_mac_address: str
    class_channel: List[str]
    serial_number: str


@dataclass
class ZigbeeExtension:
    """ Represents Zigbee extension data. """
    version_support: List[str]
    device_id: str


@dataclass
class EndpointApp:
    """ Stores information about an endpoint application. """
    id: str
    applicationType: str
    applicationName: str
    clientToken: str
    endpointURL: str
    certificateInfo: dict

    def __init__(self, json_str):
        self.id = json_str.get("id", "")
        self.applicationType = json_str.get("applicationType", "")
        self.applicationName = json_str.get("applicationName", "")
        self.clientToken = json_str.get("clientToken", "")
        self.certificateInfo = json_str.get("certificateInfo", {})
        self.endpointURL = json_str.get("meta", {}).get("location", "")

    def to_dict(self):
        """ Stores information about an endpoint application. """
        return {
            "id": self.id,
            "applicationType": self.applicationType,
            "applicationName": self.applicationName,
            "clientToken": self.clientToken,
            "certificateInfo": self.certificateInfo,
            "endpointURL": self.endpointURL
        }


@dataclass
class EndpointAppsExtension:
    """ Contains a list of endpoint applications. """
    applications: List[EndpointApp]
    deviceControlEnterpriseEndpoint: Optional[str] = None
    telemetryEnterpriseEndpoint: Optional[str] = None

    def to_dict(self):
        """ function to convert to dictionary """
        return {
            "applications": [
                {
                    "value": app["id"],
                    "$ref": app["meta"]["location"]
                } for app in self.applications
            ],
            "deviceControlEnterpriseEndpoint": self.deviceControlEnterpriseEndpoint,
            "telemetryEnterpriseEndpoint": self.telemetryEnterpriseEndpoint
        }


class Device:
    """ Represents a device with extensions and schema handling. """
    def __init__(self, deviceDisplayName: str, adminState: bool,
                 ble_extension: BleExtension,
                 schemas: List[str] =["urn:ietf:params:scim:schemas:core:2.0:Device"],
                 deviceID: str = str(uuid.uuid4()),
                 endpointAppsExtension: EndpointAppsExtension = None, **kwargs):
        self.deviceID = deviceID
        self.schemas = schemas
        self.deviceDisplayName = deviceDisplayName
        self.adminState = adminState
        self.ble_extension = ble_extension
        self.zigbeeExtension = None
        self.dppExtension = None
        self.endpointAppsExtension = endpointAppsExtension
        self.meta = kwargs.get('meta', {})

    @classmethod
    def create(cls, device_dict):
        """ function to create schemas """
        schemas = device_dict.get('schemas', [])
        deviceID = device_dict.get('id', '')
        deviceDisplayName = device_dict.get('deviceDisplayName', '')
        adminState = device_dict.get('adminState', False)
        meta = device_dict.get('meta', {})
        ble_extension = \
            device_dict.get('urn:ietf:params:scim:schemas:extension:ble:2.0:Device',
                            {})
        endpoint_apps_extension = \
            device_dict.get('urn:ietf:params:scim:schemas:extension:endpointAppsExt:2.0:Device',
                            {})
        ble_extension = BleExtension(
            ble_extension.get('deviceMacAddress', ''),
            ble_extension.get('versionSupport', []),
            ble_extension.get('isRandom', False),
            ble_extension.get('urn:ietf:params:scim:schemas:extension:pairingPassKey:2.0:Device',
                              {}).get('key', None)
        )
        endpoint_apps_dict = device_dict.get(
            'urn:ietf:params:scim:schemas:extension:endpointAppsExt:2.0:Device', {})
        application_list = [EndpointApp(app) for app in endpoint_apps_dict.get('applications', [])]

        endpoint_apps_extension = EndpointAppsExtension(
            applications=application_list,
            deviceControlEnterpriseEndpoint=endpoint_apps_dict.get(
                'deviceControlEnterpriseEndpoint', ''),
            telemetryEnterpriseEndpoint=endpoint_apps_dict.get('telemetryEnterpriseEndpoint', ''))

        return cls(deviceDisplayName, adminState, ble_extension, schemas, deviceID, endpoint_apps_extension)

    @classmethod
    def from_json(cls, json_str):
        """ convert from  json to string """
        return cls(**json.loads(json_str))

    def to_dict(self):
        """ function to convert to dictionary """
        schemas = ["urn:ietf:params:scim:schemas:core:2.0:Device"]
        if self.ble_extension is not None:
            schemas.append(
                "urn:ietf:params:scim:schemas:extension:ble:2.0:Device")
        if self.dppExtension is not None:
            schemas.append(
                "urn:ietf:params:scim:schemas:extension:dpp:2.0:Device")
        if self.zigbeeExtension is not None:
            schemas.append(
                "urn:ietf:params:scim:schemas:extension:zigbee:2.0:Device")
        if self.endpointAppsExtension is not None:
            schemas.append(
                "urn:ietf:params:scim:schemas:extension:endpointAppsExt:2.0:Device")
        return {
            "deviceID": self.deviceID,
            "deviceDisplayName": self.deviceDisplayName,
            "adminState": self.adminState,
            "schemas": schemas,
            "urn:ietf:params:scim:schemas:extension:ble:2.0:Device": self.ble_extension.to_dict() if self.ble_extension else None,
            "urn:ietf:params:scim:schemas:extension:dpp:2.0:Device": self.dppExtension.to_dict() if self.dppExtension else None,
            "urn:ietf:params:scim:schemas:extension:zigbee:2.0:Device": self.zigbeeExtension.to_dict() if self.zigbeeExtension else None,
            "urn:ietf:params:scim:schemas:extension:endpointApps:2.0:Device": self.endpointAppsExtension.to_dict() if self.endpointAppsExtension else None
        }

    def __json__(self):
        return self.to_dict()
