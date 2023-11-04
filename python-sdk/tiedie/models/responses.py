#!python
# Copyright (c) 2023, Cisco Systems, Inc. and/or its affiliates.
# All rights reserved.
# See LICENSE file in this distribution.
# SPDX-License-Identifier: Apache-2.0
"""

This Python module manages Tiedie IoT platform responses and requests, 
including handling Tiedie responses, data responses, and discovery-related inteactions.

"""

import json
from enum import Enum


class TiedieStatus(Enum):
    """ Enum representing success and failure status. """
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    

class TiedieResponse:
    """ Class for handling Tiedie API response data. """
    def __init__(self):
        self.status = None
        self.reason = None
        self.errorCode = None
        self.body = None
        self.httpStatusCode = None
        self.httpMessage = None
        self.map = {}


    def unpack_remaining(self, key, value):
        """ function to upack corrosponding to the key """
        self.map[key] = value


    def __json__(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)
    
    
class DataResponse:
    """ Class for data response with value and status. """
    def __init__(self, value = None, status = None):
        self.value = value
        self.status = status


    def __json__(self):
        return self.__dict__()
    
    
    def __dict__(self):
        return {
            "value": self.value,
            "status": self.status
        }


class DiscoverRequest:
    """ Class for making a discover request. """
    def __init__(self):
        self.serviceUUID = ""
        self.characteristicUUID = ""
        self.descriptorUUID = ""


class DiscoverResponse:
    """ Class for handling the response of a discovery. """
    def __init__(self):
        self.data_parameters = []
