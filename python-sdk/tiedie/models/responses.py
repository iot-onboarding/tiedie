#!python
# Copyright (c) 2023, Cisco Systems, Inc. and/or its affiliates.
# All rights reserved.
# See LICENSE file in this distribution.
# SPDX-License-Identifier: Apache-2.0

import json
from enum import Enum
from .ble import BleDataParameter


class TiedieStatus(Enum):
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"


class ListResponse:
    totalResults: int
    startIndex: int
    itemsPerPage: int
    resources: list

    @classmethod
    def from_json(cls, json_str):
        return cls(json.loads(json_str))
    
    
class EndpointAppListResponse:
    totalResults: int
    startIndex: int
    itemsPerPage: int
    resources: list
    

class TiedieResponse:
    def __init__(self):
        self.status = None
        self.reason = None
        self.errorCode = None
        self.body = None
        self.httpStatusCode = None
        self.httpMessage = None
        self.requestID = None
        self.map = {}


    def unpack_remaining(self, key, value):
        self.map[key] = value


    def __json__(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)


class DiscoverResponse:
    def __init__(self, httpStatusCode = None):
        self.httpStatusCode = httpStatusCode
        self.services = []

    def get_services(self, id, json_data):
        for service in json_data.get("services", ""):
            for characteristic in service["characteristics"]:
                self.services.append(BleDataParameter(id, service.get('serviceID'), characteristic.get('characteristicID'), characteristic.get('flags')))
    
    
class DataResponse(TiedieResponse):
    def __init__(self, value = None, status = None):
        super().__init__()
        self.value = value


    def __json__(self):
        return self.__dict__()
    
    
    def __dict__(self):
        return {
            "value": self.value,
            "status": self.status,
            "errorCode": self.errorCode if self.errorCode else None,
            "reason": self.reason if self.reason else None
        }

class RegistrationResponse(TiedieResponse):
    def __init__(self, topic = None):
        super().__init__()
        self.topic = topic


    def __json__(self):
        return self.__dict__()
    
    
    def __dict__(self):
        return {
            "status": self.status,
            "topic" : self.topic,
            "errorCode": self.errorCode if self.errorCode else None,
            "reason": self.reason if self.reason else None,
        }