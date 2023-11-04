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
import json 


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
   An enumeration class representing data formats, including JSON and XML.
   """
   JSON = "json"
   XML = "xml"

    def __json__(self):
        return self.value
    

class DataParameter:
    """ A class for storing data parameters, with a device_id attribute. """
    def __init__(self, device_id: str):
        self.device_id = device_id

    
    def __str__(self):
        return str(self.__dict__())
    

    def __dict__(self):
        return {"deviceId": self.device_id}
    
    
    def __json__(self):
        return json.dumps(self.__dict__())
    

class ListResponse:
    """
    A class representing a list response with attributes for totalResults,
    startIndex, itemsPerPage, and resources.
    """
    totalResults: int
    startIndex: int
    itemsPerPage: int
    resources: list

    @classmethod
    def from_json(cls, json_str):
        return cls(json.loads(json_str))
    
    
class EndpointAppListResponse:
    """
    A class representing a list response specific to endpoint applications.
    """
    totalResults: int
    startIndex: int
    itemsPerPage: int
    resources: list
    
    
class SubscriptionOptions:
    """
    A class for specifying subscription options, including topic,
    dataFormat, minReportTime, and maxReportTime.
    """
    def __init__(self, topic: str = None, dataFormat: DataFormat = None,
                 minReportTime: int = None, maxReportTime: int = None):
        self.topic = topic
        self.dataFormat = dataFormat
        self.minReportTime = minReportTime
        self.maxReportTime = maxReportTime


    def __json__(self):
        return self.__dict__()
    
    
    def __dict__(self):
        return {
            "topic": self.topic,
            "dataFormat": self.dataFormat,
            "minReportTime": self.minReportTime,
            "maxReportTime": self.maxReportTime
        }
    
