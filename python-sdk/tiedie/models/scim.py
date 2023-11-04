#!python
# Copyright (c) 2023, Cisco Systems, Inc. and/or its affiliates. 
# All rights reserved.
# See LICENSE file in this distribution.
# SPDX-License-Identifier: Apache-2.0

import json
import uuid
import attr
from typing import Any, List
from dataclasses import dataclass, field


@dataclass
class PairingJustWorks:
    key: str = "null"


@dataclass
class PairingPassKey:
    key: int


@dataclass
class PairingOOB:
    key: str
    randNumber: int
    confirmationNumber: str


@dataclass
class BleExtension:
    version_support: List[str] = field(default_factory=list)
    device_mac_address: str = ""
    address_type: bool = False
    pairing_methods: List[str] = field(default_factory=list)
    null_pairing: bool = False
    pairing_just_works: PairingJustWorks = None
    pairing_pass_key: PairingPassKey = None
    pairing_oob: PairingOOB = None


    def __init__(self, device_mac_address: str, version_support: List[str], is_random: bool, null_pair: bool = False,
                  just_works: bool = False, pass_key: int = None, oob_key: str = None, oob_random_number: str = None):
        self.schemas = ["urn:ietf:params:scim:schemas:extension:ble:2.0:Device"]
        self.device_mac_address = device_mac_address
        self.address_type = is_random
        self.version_support = version_support
        self.pairing_methods = []
        self.null_pairing = null_pair
        self.pairing_just_works = just_works
        if null_pair:
            self.pairing_methods.append("urn:ietf:params:scim:schemas:extension:pairingNull:2.0:Device")
        if just_works:
            self.pairing_methods.append("urn:ietf:params:scim:schemas:extension:pairingJustWorks:2.0:Device")
            self.pairing_just_works = PairingJustWorks()
        if pass_key:
            self.pairing_methods.append("urn:ietf:params:scim:schemas:extension:pairingPassKey:2.0:Device")
            self.pairing_pass_key = PairingPassKey(pass_key)
        if oob_key:
            self.pairing_methods.append("urn:ietf:params:scim:schemas:extension:pairingOOB:2.0:Device")
            self.pairing_oob = PairingOOB(oob_key, oob_random_number)


    @classmethod
    def from_dict(cls, data):
        null_pairing = data.pop("urn:ietf:params:scim:schemas:extension:pairingNull:2.0:Device", None)
        if null_pairing:
            cls.null_pairing = True

        pairing_just_works = data.pop("urn:ietf:params:scim:schemas:extension:pairingJustWorks:2.0:Device", None)
        if pairing_just_works:
            cls.pairing_just_works = PairingJustWorks(**pairing_just_works)

        pairing_pass_key = data.pop("urn:ietf:params:scim:schemas:extension:pairingPassKey:2.0:Device", None)
        if pairing_pass_key:
            cls.pairing_pass_key = PairingPassKey(**pairing_pass_key)

        pairing_oob = data.pop("urn:ietf:params:scim:schemas:extension:pairingOOB:2.0:Device", None)
        if pairing_oob:
            cls.pairing_oob = PairingOOB(**pairing_oob)

        cls.version_support = data.pop("versionSupport", [])
        cls.device_mac_address = data.pop("deviceMacAddress", "")
        cls.address_type = data.pop("isRandom", "")
        cls.pairing_methods = data.pop("pairingMethods", [])

        return cls


    def to_dict(self):
        data = {
            "versionSupport": self.version_support,
            "deviceMacAddress": self.device_mac_address,
            "isRandom": self.address_type,
            "pairingMethods": self.pairing_methods
        }
        if self.null_pairing:
            data["urn:ietf:params:scim:schemas:extension:pairingNull:2.0:Device"] = "null"
        if self.pairing_just_works:
            data["urn:ietf:params:scim:schemas:extension:pairingJustWorks:2.0:Device"] = self.pairing_just_works.__dict__
        if self.pairing_pass_key:
            data["urn:ietf:params:scim:schemas:extension:pairingPassKey:2.0:Device"] = self.pairing_pass_key.__dict__
        if self.pairing_oob:
            data["urn:ietf:params:scim:schemas:extension:pairingOOB:2.0:Device"] = self.pairing_oob.__dict__
        return data


    def __json__(self):
        return self.to_dict()
    

    def __str__(self):
        return str(self.__json__())
    

@attr.dataclass
class DppExtension:
    dpp_version: int
    bootstrapping_method: List[str]
    bootstrap_key: str
    device_mac_address: str
    class_channel: List[str]
    serial_number: str


@attr.dataclass
class ZigbeeExtension:
    version_support: List[str]
    device_id: str


@dataclass
class EndpointApp:
    id: str
    applicationType: str
    applicationName: str
    clientToken: str
    endpointURL: str


    def __init__(self, json_str):
        self.id = json_str.get("id", "")
        self.applicationType = json_str.get("applicationType", "")
        self.applicationName = json_str.get("applicationName", "")
        self.clientToken = json_str.get("clientToken", "")
        if json_str.get("meta"):
            self.endpointURL = json_str.get("meta").get("location", "")
        else:
            self.endpointURL = ""
        

    def to_dict(self):
        return {
            "id": self.id,  
            "applicationType": self.applicationType,
            "applicationName": self.applicationName,
            "clientToken": self.clientToken,
            "endpointURL": self.endpointURL
        }


@dataclass
class EndpointAppsExtension:
    onboardingUrl: str
    deviceControl: List[str]
    dataReceiver: List[str]

    def to_dict(self):
        return {
            "onboardingUrl": self.onboardingUrl,
            "deviceControlUrl":[app for app in self.deviceControl],
            "dataReceiverUrl": [app for app in self.dataReceiver]
        }
    
    @classmethod
    def from_dict(cls, data):
        cls.onboardingUrl = data.get("onboardingUrl", "")
        cls.deviceControl = data.get("deviceControlUrl", [])
        cls.dataReceiver = data.get("dataReceiverUrl", [])

        return cls

    

class Device:
    def __init__(self, deviceDisplayName: str, adminState: bool, ble_extension: BleExtension, schemas: List[str] =["urn:ietf:params:scim:schemas:core:2.0:Device"], 
                 id: str = None, endpointAppsExtension: EndpointAppsExtension = None, zigbeeExtension: ZigbeeExtension = None, dppExtension: DppExtension = None):
        self.deviceID = id 
        self.schemas = schemas
        self.deviceDisplayName = deviceDisplayName
        self.adminState = adminState
        self.ble_extension = ble_extension
        self.zigbeeExtension = zigbeeExtension
        self.dppExtension = dppExtension
        self.endpointAppsExtension = endpointAppsExtension


    @classmethod
    def create(cls, device_dict):
        schemas = device_dict.get('schemas', [])
        deviceID = device_dict.get('id', '')
        deviceDisplayName = device_dict.get('deviceDisplayName', '')
        adminState = device_dict.get('adminState', False)
        ble_extension = device_dict.get('urn:ietf:params:scim:schemas:extension:ble:2.0:Device', {})
        endpoint_apps_extension = device_dict.get('urn:ietf:params:scim:schemas:extension:endpointAppsExt:2.0:Device', {})
        ble_extension = BleExtension.from_dict(ble_extension)
        endpoint_apps_dict = device_dict.get('urn:ietf:params:scim:schemas:extension:endpointAppsExt:2.0:Device', {})
        endpoint_apps_extension = EndpointAppsExtension.from_dict(endpoint_apps_dict)
        
        return cls(deviceDisplayName, adminState, ble_extension, schemas, deviceID, endpoint_apps_extension)
       

    @classmethod
    def from_json(cls, json_str):
        return cls(**json.loads(json_str))


    def to_dict(self):
        schemas = ["urn:ietf:params:scim:schemas:core:2.0:Device"]
        resp = {
            "deviceDisplayName": self.deviceDisplayName,
            "adminState": self.adminState,
            "schemas": schemas
        }
        if self.ble_extension is not None:
            resp["schemas"].append("urn:ietf:params:scim:schemas:extension:ble:2.0:Device")
            resp["urn:ietf:params:scim:schemas:extension:ble:2.0:Device"] = self.ble_extension.to_dict()
        if self.dppExtension is not None:
            resp["schemas"].append("urn:ietf:params:scim:schemas:extension:dpp:2.0:Device")
            resp["urn:ietf:params:scim:schemas:extension:dpp:2.0:Device"] = self.dppExtension.to_dict()
        if self.zigbeeExtension is not None:
            resp["schemas"].append("urn:ietf:params:scim:schemas:extension:zigbee:2.0:Device")
            resp["urn:ietf:params:scim:schemas:extension:zigbee:2.0:Device"] = self.zigbeeExtension.to_dict()
        if self.endpointAppsExtension is not None:
            resp["schemas"].append("urn:ietf:params:scim:schemas:extension:endpointAppsExt:2.0:Device")
            resp["urn:ietf:params:scim:schemas:extension:endpointAppsExt:2.0:Device"] = self.endpointAppsExtension.to_dict()
   
        return resp


    def __json__(self):
        return self.to_dict()
    

    