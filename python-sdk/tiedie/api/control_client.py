#!python
# Copyright (c) 2023, Cisco and/or its affiliates.
# All rights reserved.
# See LICENSE file in this distribution.
# SPDX-License-Identifier: Apache-2.0

"""

This module defines a Python client for making HTTP requests to a
control servie, specifically for managing IoT devices. It includes
various functions for devicemanagement, data communication, and
registration processes.

"""

from typing import List, Optional

from tiedie.models.ble import DataParameter
from tiedie.models.common import RegistrationOptions
from tiedie.models.requests import (
    BleConnectRequest,
    IDQuery,
    Technology,
    TiedieBasicRequest,
    TiedieConnectRequest,
    TiedieReadRequest,
    TiedieRegisterTopicRequest,
    TiedieWriteRequest,
    TopicQuery)
from tiedie.models.responses import (
    BleDiscoverResponse, TiedieResponse, ValueResponse)
from tiedie.models.scim import Device
from tiedie.models.zigbee import ZigbeeDiscoverResponse

from .auth import Authenticator
from .http_client import AbstractHttpClient


class ControlClient(AbstractHttpClient):
    """ Performs IoT device control and data management operations. """

    def __init__(self, base_url: str, authenticator: Authenticator):
        super().__init__(base_url, "application/scim+json", authenticator)
        self.base_url = base_url
        self.authenticator = authenticator

    def create_binding(self, device: Device) -> TiedieResponse[None]:
        """Create a binding for the device.

        Args:
            device (Device): The device to create a binding for.

        Returns:
            TiedieResponse[IDQuery]: Response with the ID of the device.
        """
        tiedie_request = TiedieBasicRequest(device=device)
        return self.post_with_tiedie_response('/connectivity/binding',
                                              tiedie_request,
                                              None)

    def connect(self, device: Device,
                request: Optional[BleConnectRequest] = None) \
            -> TiedieResponse[Optional[List[DataParameter]]]:
        """Initiates a connection with an IoT device and retrieves GATT
        services.

        Raises:
            ValueError: Raised if device ID is not present in the device

        Returns:
            TiedieResponse[Optional[List[DataParameter]]]: The `TieDieResponse` object contains
            the state of the request. 
            A list of DataParameter objects is present if the service discovery was successful.

        """
        if device.device_id is None:
            raise ValueError("Device ID is required for connection")

        if request is None:
            request = BleConnectRequest(services=None,
                                        retries=3,
                                        retry_multiple_aps=True)

        tiedie_request = TiedieConnectRequest(device=device, ble=request)

        ble_discover_response = self.post_with_tiedie_response(
            '/connectivity/connection', tiedie_request, BleDiscoverResponse)

        tiedie_response = TiedieResponse[Optional[List[DataParameter]]](
            http=ble_discover_response.http,
            status=ble_discover_response.status,
            reason=ble_discover_response.reason,
            error_code=ble_discover_response.error_code,
        )
        if isinstance(ble_discover_response, BleDiscoverResponse) and \
                ble_discover_response.services is not None and \
                ble_discover_response.services != []:
            parameter_list = ble_discover_response.to_parameter_list(
                device.device_id)
            tiedie_response.body = parameter_list

        return tiedie_response

    def disconnect(self, device: Device) -> TiedieResponse[None]:
        """ Disconnects from a connected IoT device. """
        return self.delete_with_tiedie_response('/connectivity/connection',
                                                IDQuery(device_id=device.device_id), None)

    def discover(self, device: Device,
                 request: Optional[BleConnectRequest] = None) \
            -> TiedieResponse[Optional[List[DataParameter]]]:
        """Discovers services and characteristics of an IoT device. 

        Raises:
            ValueError: Raised if device ID is not present in the device

        Returns:
            TiedieResponse[Optional[List[DataParameter]]]: The `TieDieResponse` object contains
            the state of the request. 
            A list of DataParameter objects is present if the service discovery was successful.
        """
        if device.device_id is None:
            raise ValueError("Device ID is required for connection")

        if request is None:
            request = BleConnectRequest(services=None,
                                        retries=3,
                                        retry_multiple_aps=True)

        tiedie_request = TiedieConnectRequest(device=device, ble=request)

        if tiedie_request.technology == Technology.BLE:
            ble_discover_response = self.get_with_tiedie_response(
                "/connectivity/services", tiedie_request, BleDiscoverResponse)
            tiedie_response = TiedieResponse[Optional[List[DataParameter]]](
                http=ble_discover_response.http,
                status=ble_discover_response.status,
                reason=ble_discover_response.reason,
                error_code=ble_discover_response.error_code,
            )
            if isinstance(ble_discover_response, BleDiscoverResponse) and \
                    ble_discover_response.services is not None and \
                    ble_discover_response.services != []:
                parameter_list = ble_discover_response.to_parameter_list(
                    device.device_id)
                tiedie_response.body = parameter_list

            return tiedie_response

        zigbee_discover_response = self.post_with_tiedie_response(
            "/connection/services", tiedie_request, ZigbeeDiscoverResponse)

        tiedie_response = TiedieResponse[Optional[List[DataParameter]]](
            http=zigbee_discover_response.http,
            status=zigbee_discover_response.status,
            reason=zigbee_discover_response.reason,
            error_code=zigbee_discover_response.error_code,
        )
        if isinstance(zigbee_discover_response, ZigbeeDiscoverResponse) and \
                zigbee_discover_response.endpoints is not None and \
                zigbee_discover_response.endpoints != []:
            parameter_list = zigbee_discover_response.to_parameter_list(
                device.device_id)
            tiedie_response.body = parameter_list

        return tiedie_response

    def read(self, device: Device, data_parameter: DataParameter) -> ValueResponse:
        """ Reads the value of a GATT characteristic of an IoT device. """
        tiedie_request = \
            TiedieReadRequest(device=device, data_parameter=data_parameter)
        return self.get_with_tiedie_response("/data/attribute",
                                             tiedie_request, ValueResponse)

    def write(self, device: Device,
              data_parameter: DataParameter,
              value: str) -> ValueResponse:
        """ Writes a value to a GATT characteristic of an IoT device. """
        tiedie_request = TiedieWriteRequest(device=device,
                                            data_parameter=data_parameter,
                                            value=value)
        return self.post_with_tiedie_response("/data/attribute",
                                              tiedie_request, ValueResponse)

    def subscribe(self, device: Device, data_parameter: DataParameter) -> TiedieResponse[None]:
        """ Subscribes to a data stream topic for an IoT device. """
        tiedie_request = TiedieReadRequest(device=device,
                                           data_parameter=data_parameter)
        return self.post_with_tiedie_response("/data/subscription",
                                              tiedie_request, None)

    def unsubscribe(self, device: Device, data_parameter: DataParameter) -> TiedieResponse[None]:
        """ Unsubscribes from a data stream topic for an IoT device. """
        tiedie_request = TiedieReadRequest(device=device,
                                           data_parameter=data_parameter)
        return self.delete_with_tiedie_response("/data/subscription",
                                                tiedie_request, None)

    def register_topic(self,
                       topic: str,
                       device: Optional[Device] = None,
                       options: Optional[RegistrationOptions] = None) -> TiedieResponse[None]:
        """ Registers a data stream topic for an IoT device. """
        tiedie_request = \
            TiedieRegisterTopicRequest(topic=topic, device=device, registration_options=options)
        return self.post_with_tiedie_response("/registration/topic",
                                              tiedie_request, None)

    def unregister_topic(self, topic: str):
        """ Unregisters a data stream topic for IoT devices. """
        return self.delete_with_tiedie_response("/registration/topic",
                                                TopicQuery(topic=topic), None)
