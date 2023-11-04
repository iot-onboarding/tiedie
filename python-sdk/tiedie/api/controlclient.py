#!python
# Copyright (c) 2023, Cisco Systems, Inc. and/or its affiliates.
# All rights reserved.
# See LICENSE file in this distribution.
# SPDX-License-Identifier: Apache-2.0
"""

This module defines a Python client for making HTTP requests to a
control servie, specifically for managing IoT devices. It includes
various functions for devicemanagement, data communication, and
registration processes.

"""

import json
import requests

from .auth import Authenticator
from tiedie.models.request import (TiedieBasicRequest, TiedieConnectRequest,
                                   BleConnectRequest, BleDiscoverResponse,
                                   ZigbeeDiscoverResponse, Technology,
                                   TiedieReadRequest, TiedieWriteRequest,
                                   TiedieSubscribeRequest,
                                   TiedieUnsubscribeRequest,
                                   TiedieRegisterTopicRequest,
                                   TiedieUnregisterTopicRequest,
                                   TiedieRegisterDataAppRequest)
from tiedie.models.responses import (DataResponse, TiedieResponse) 
from tiedie.models.scim import Device
from tiedie.models.ble import DataParameter
from .httpclient import AbstractHttpClient


class ControlClient(AbstractHttpClient):
    """ Performs IoT device control and data management operations. """
    def __init__(self, base_url: str, authenticator: Authenticator):
        super().__init__(base_url, "application/scim+json", authenticator)
        self.base_url = base_url 
        self.authenticator = authenticator
        self.control_app_id = authenticator.get_client_id()


    def introduce(self, device: Device):
        """ Introduces an IoT device to the application. """
        tiedie_request = TiedieBasicRequest.create_request(device,
                                                           self.control_app_id)
        return self.post_with_tiedie_response('/connectivity/introduce',
                                                  tiedie_request,
                                                  TiedieResponse)

    def connect(self, device: Device, request: BleConnectRequest = None,
                services = None):
        """
        Initiates a connection with an IoT device and retrieves GATT
        services.
        """
        if not request:
            request = BleConnectRequest(services, 3, True)

        tiedie_request = TiedieConnectRequest.create_request(device,
                                                             request,
                                                             self.control_app_id)
        ble_discover_response = \
            self.post_with_tiedie_response('/connectivity/connect',
                                           tiedie_request, BleDiscoverResponse)
        response = TiedieResponse()
        response.httpStatusCode = ble_discover_response.http_status_code
        response.httpMessage = ble_discover_response.http_message
        response.status =   getattr(ble_discover_response, "status", None)
        response.reason =  getattr(ble_discover_response, "reason", None)
        if respone.status == 'FAILURE':
            response.errorCode = ble_discover_response.http_status_code
        else:
            response.errorCode = None

        if response.status != 'FAILURE' and ble_discover_response \
           and getattr(ble_discover_response.body, "services", None) != None:
            response.body = \
                ble_discover_response.body.toParameterList(device.get('id'))
        return response
    

    def disconnect(self, device: Device):
        """ Disconnects from a connected IoT device. """
        tiedie_request = TiedieBasicRequest.create_request(device,
                                                           self.control_app_id)
        return self.post_with_tiedie_response('/connectivity/disconnect',
                                              tiedie_request, TiedieResponse)

    def discover(self, device):
        """ Discovers services and characteristics of an IoT device. """
        tiedie_request = TiedieBasicRequest.create_request(device,
                                                           self.control_app_id)

        if tiedie_request.technology == Technology.BLE.value:
            ble_discover_response = \
                self.post_with_tiedie_response("/data/discover",
                                               tiedie_request,
                                               BleDiscoverResponse)
            response = TiedieResponse()
            response.httpStatusCode = ble_discover_response.http_status_code
            response.httpMessage = ble_discover_response.http_message
            response.status =   getattr(ble_discover_response, "status", None)
            response.reason =  getattr(ble_discover_response, "reason", None)
            if response.status == 'FAILURE':
                response.errorCode = ble_discover_response.http_status_code
            else:
                response.status = None
            if response.status != 'FAILURE' and ble_discover_response \
               and getattr(ble_discover_response.body, "services", None) != None:
                response.body = \
                    ble_discover_response.body.toParameterList(device.get('id'))
            return response

        zigbee_discover_response = \
            self.post_with_tiedie_response("/data/discover",
                                           tiedie_request,
                                           ZigbeeDiscoverResponse)

        response = TiedieResponse()
        response.httpStatusCode = zigbee_discover_response.httpStatusCode
        response.httpMessage = zigbee_discover_response.httpMessage
        response.status = zigbee_discover_response.status
        response.reason = zigbee_discover_response.reason
        response.errorCode = zigbee_discover_response.errorCode

        if zigbee_discover_response != None and \
           zigbee_discover_response.endpoints != None:
            response.body = \
                zigbee_discover_response.to_parameter_list(device.getId())
        return response
    

    def read(self, data_parameter):
        """ Reads the value of a GATT characteristic of an IoT device. """
        tiedie_request = \
            TiedieReadRequest.create_request(data_parameter,
                                             self.control_app_id)
        return self.post_with_tiedie_response("/data/read",
                                                  tiedie_request, DataResponse)

    def write(self, data_parameter, value):
        """ Writes a value to a GATT characteristic of an IoT device. """
        tiedie_request=TiedieWriteRequest.create_request(data_parameter,
                                                         value,
                                                         self.control_app_id)
        return self.post_with_tiedie_response("/data/write",
                                              tiedie_request,DataResponse)

    def subscribe(self, topic, data_parameter, options=None):
        """ Subscribes to a data stream topic for an IoT device. """
        tiedie_request = TiedieSubscribeRequest.create_request(topic,
                                                               data_parameter,
                                                               self.control_app_id,
                                                               options)
        return self.post_with_tiedie_response("/data/subscribe",
                                              tiedie_request, DataResponse)

    def unsubscribe(self, data_parameter, options=None):
        """ Unsubscribes from a data stream topic for an IoT device. """
        tiedie_request= \
            TiedieUnsubscribeRequest.create_request(data_parameter,
                                                    self.control_app_id)
        return self.post_with_tiedie_response("/data/unsubscribe",
                                              tiedie_request, DataResponse)
    
    def register_topic(self, topic, options=None):
        """ Registers a data stream topic for an IoT device. """
        tiedie_request= \
            TiedieRegisterTopicRequest.create_request(topic,options,
                                                      self.control_app_id)
        return self.post_with_tiedie_response("/registration/registerTopic",
                                              tiedie_request, DataResponse)

    def unregister_topic(self, topic, devices):
        """ Unregisters a data stream topic for IoT devices. """
        tiedie_request=TiedieUnregisterTopicRequest.create_request(topic,devices,self.control_app_id)
        return self.post_with_tiedie_response("/registration/unregisterTopic",
                                              tiedie_request, DataResponse)

    def register_data_app(self, data_app, topic:DataParameter):
        """ Registers a data app for IoT device communication. """
        tiedie_request = \
            TiedieRegisterDataAppRequest.create_request(data_app, topic,
                                                        self.control_app_id)
        return self.post_with_tiedie_response("/registration/registerDataApp",
                                              tiedie_request, DataResponse)
