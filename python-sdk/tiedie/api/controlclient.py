#!python
# Copyright (c) 2023, Cisco Systems, Inc. and/or its affiliates.
# All rights reserved.
# See LICENSE file in this distribution.
# SPDX-License-Identifier: Apache-2.0

from ..api.auth import Authenticator
from ..models.request import (TiedieBasicRequest, TiedieConnectRequest, TiedieDiscoverRequest, TiedieUnregisterDataAppRequest,
                                   TiedieReadRequest, TiedieWriteRequest, TiedieSubscribeRequest, TiedieUnsubscribeRequest,
                                   TiedieRegisterTopicRequest, TiedieUnregisterTopicRequest, TiedieRegisterDataAppRequest)
from ..models.responses import (DataResponse, TiedieResponse, DiscoverResponse, RegistrationResponse) 
from ..models.scim import Device
from ..models.ble import BleServicesRequest
from ..api.httpclient import AbstractHttpClient


class ControlClient(AbstractHttpClient):
    def __init__(self, base_url: str, authenticator: Authenticator):
        super().__init__(base_url, "application/json", authenticator)
        self.base_url = base_url 
        self.authenticator = authenticator
        self.control_app_id = authenticator.get_client_id()


    def introduce(self, device: Device):
        tiedie_request = TiedieBasicRequest.create_request(device, self.control_app_id)
        response = self.post_with_tiedie_response('/connectivity/introduce', tiedie_request, TiedieResponse)
        return response
    

    def connect(self, device: Device, request: BleServicesRequest = None, services = None):
        if not request:
            request = BleServicesRequest(services)

        tiedie_request = TiedieConnectRequest.create_request(device, request, self.control_app_id, 3, True)
        ble_discover_response = self.post_with_tiedie_response('/connectivity/connect', tiedie_request, TiedieResponse)

        if ble_discover_response.httpStatusCode == 200:
    
            response = DiscoverResponse(ble_discover_response.httpStatusCode)
            response.get_services(device.get('id'), ble_discover_response.map)
            return response
        
        else:
            return ble_discover_response
    

    def disconnect(self, device: Device):
        tiedie_request = TiedieBasicRequest.create_request(device, self.control_app_id)
        response = self.post_with_tiedie_response('/connectivity/disconnect', tiedie_request, TiedieResponse)
        return response
    

    def discover(self, device, services = None):
        request = BleServicesRequest(services)
        tiedie_request = TiedieDiscoverRequest.create_request(device, request, self.control_app_id, 3, True)
        ble_discover_response = self.post_with_tiedie_response("/data/discover", tiedie_request, TiedieResponse)

        if ble_discover_response.httpStatusCode == 200:
            response = DiscoverResponse(ble_discover_response.httpStatusCode)
            response.get_services(device.get('id'), ble_discover_response.map)
            return response
        
        else:
            return ble_discover_response


    def read(self, data_parameter):
        tiedie_request = TiedieReadRequest.create_request(data_parameter, self.control_app_id)
        response = self.post_with_tiedie_response("/data/read", tiedie_request, DataResponse)
        return response.map
    

    def write(self, data_parameter, value):
        tiedie_request = TiedieWriteRequest.create_request(data_parameter, value, self.control_app_id)
        response = self.post_with_tiedie_response("/data/write", tiedie_request, DataResponse)
        return response.map


    def subscribe(self, topic, data_parameter, options=None):
        tiedie_request = TiedieSubscribeRequest.create_request(topic, data_parameter, self.control_app_id, options)
        response = self.post_with_tiedie_response("/data/subscribe", tiedie_request, TiedieResponse)
        return response
    

    def unsubscribe(self, topic, data_parameter, options=None):
        tiedie_request = TiedieUnsubscribeRequest.create_request(topic, data_parameter, self.control_app_id)
        response = self.post_with_tiedie_response("/data/unsubscribe", tiedie_request, TiedieResponse)
        return response
    

    def register_data_app(self, data_app:list(), topic):
        tiedie_request = TiedieRegisterDataAppRequest(topic, data_app, self.control_app_id)
        response = self.post_with_tiedie_response("/registration/registerDataApp", tiedie_request, RegistrationResponse)
        return response
    

    def unregister_data_app(self, data_app, topic):
        tiedie_request = TiedieUnregisterDataAppRequest(topic, data_app, self.control_app_id)
        response = self.post_with_tiedie_response("/registration/unregisterDataApp", tiedie_request, RegistrationResponse)
        return response
    
    
    def register_topic(self, topic, options=None):
        tiedie_request = TiedieRegisterTopicRequest.create_request(topic, options, self.control_app_id)
        response = self.post_with_tiedie_response("/registration/registerTopic", tiedie_request, RegistrationResponse)
        return response
    

    def unregister_topic(self, topic, devices):
        tiedie_request = TiedieUnregisterTopicRequest.create_request(topic, devices, self.control_app_id)
        response = self.post_with_tiedie_response("/registration/unregisterTopic", tiedie_request, RegistrationResponse)
        return response
