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

from typing import Optional, Sequence

from tiedie.models.ble import DataParameter
from tiedie.models.common import RegistrationOptions
from tiedie.models.requests import (
    BleConnectRequest,
    IDQuery,
    Technology,
    TiedieConnectRequest,
    TiedieReadRequest,
    TiedieRegisterTopicRequest,
    TiedieWriteRequest,
    TopicQuery)
from tiedie.models.responses import (
    BleDiscoverResponse, MultiConnectionsResponse, TiedieResponse, ValueResponse)
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

    def connect(self, device: Device,
                request: BleConnectRequest = BleConnectRequest(),
                retries=3,
                retry_multiple_aps=True) \
            -> TiedieResponse[Optional[Sequence[DataParameter]]]:
        """Initiates a connection with an IoT device and retrieves GATT
        services.

        Args:
            device (Device): The device to connect to.
            request (BleConnectRequest, optional): The connection request object. 
                Defaults to None.
            retries (int, optional): The number of times to retry the connection. 
                Defaults to 3.
            retry_multiple_aps (bool, optional): Whether to retry the connection with multiple 
                access points. Defaults to True.

        Raises:
            ValueError: Raised if device ID is not present in the device

        Returns:
            TiedieResponse[Optional[Sequence[DataParameter]]]: The `TieDieResponse` object contains
            the state of the request. 
            A list of DataParameter objects is present if the service discovery was successful.

        """
        if device.device_id is None:
            raise ValueError("Device ID is required for connection")

        tiedie_request = TiedieConnectRequest(
            device=device,
            ble=request,
            retries=retries,
            retry_multiple_aps=retry_multiple_aps)

        ble_discover_response = self.post_with_tiedie_response(
            '/connectivity/connection', tiedie_request, BleDiscoverResponse)

        tiedie_response = TiedieResponse[Optional[Sequence[DataParameter]]](
            http=ble_discover_response.http,
            status=ble_discover_response.status,
            reason=ble_discover_response.reason,
            error_code=ble_discover_response.error_code,
        )
        if isinstance(ble_discover_response.body, BleDiscoverResponse) and \
                ble_discover_response.body.services is not None and \
                ble_discover_response.body.services != []:
            parameter_list = ble_discover_response.body.to_parameter_list(
                device.device_id)
            tiedie_response.body = parameter_list

        return tiedie_response

    def disconnect(self, *device: Device) -> TiedieResponse[Optional[MultiConnectionsResponse]]:
        """ Disconnects from a connected IoT device. """
        return self.delete_with_tiedie_response('/connectivity/connection',
                                                IDQuery(device_ids=[
                                                    d.device_id for d in device
                                                ]), MultiConnectionsResponse)

    def discover(self, device: Device,
                 request=BleConnectRequest(),
                 retries=3,
                 retry_multiple_aps=True) \
            -> TiedieResponse[Optional[Sequence[DataParameter]]]:
        """Discovers services and characteristics of an IoT device. 

        Raises:
            ValueError: Raised if device ID is not present in the device

        Args:
            device (Device): The device to discover.
            request (BleConnectRequest, optional): The connection request object. 
                Defaults to None.
            retries (int, optional): The number of times to retry the connection.
            retry_multiple_aps (bool, optional): Whether to retry the connection with multiple
                access points.

        Returns:
            TiedieResponse[Optional[Sequence[DataParameter]]]: The `TieDieResponse` object contains
            the state of the request. 
            A list of DataParameter objects is present if the service discovery was successful.
        """
        if device.device_id is None:
            raise ValueError("Device ID is required for connection")

        tiedie_request = TiedieConnectRequest(
            device=device, ble=request, retries=retries, retry_multiple_aps=retry_multiple_aps)

        if tiedie_request.technology == Technology.BLE:
            ble_discover_response = self.post_with_tiedie_response(
                "/connectivity/services", tiedie_request, BleDiscoverResponse)
            tiedie_response = TiedieResponse[Optional[Sequence[DataParameter]]](
                http=ble_discover_response.http,
                status=ble_discover_response.status,
                reason=ble_discover_response.reason,
                error_code=ble_discover_response.error_code,
            )
            if isinstance(ble_discover_response.body, BleDiscoverResponse) and \
                    ble_discover_response.body.services is not None and \
                    ble_discover_response.body.services != []:
                parameter_list = ble_discover_response.body.to_parameter_list(
                    device.device_id)
                tiedie_response.body = parameter_list

            return tiedie_response

        zigbee_discover_response = self.post_with_tiedie_response(
            "/connection/services", tiedie_request, ZigbeeDiscoverResponse)

        tiedie_response = TiedieResponse[Optional[Sequence[DataParameter]]](
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

    def read(self, device: Device, data_parameter: DataParameter) \
            -> TiedieResponse[Optional[ValueResponse]]:
        """ Reads a value from a GATT characteristic of an IoT device.

        Args:
            device (Device): The device to read from.
            data_parameter (DataParameter): The data parameter to read.

        Returns:
            ValueResponse: The response object containing the value.
        """
        tiedie_request = \
            TiedieReadRequest(device=device, data_parameter=data_parameter)
        return self.post_with_tiedie_response("/data/attribute/read",
                                              tiedie_request, ValueResponse)

    def write(self, device: Device,
              data_parameter: DataParameter,
              value: str) -> TiedieResponse[Optional[ValueResponse]]:
        """ Writes a value to a GATT characteristic of an IoT device.

        Args:
            device (Device): The device to write to.
            data_parameter (DataParameter): The data parameter to write to.
            value (str): The value to write.

        Returns:
            ValueResponse: The response object containing the value.
        """
        tiedie_request = TiedieWriteRequest(device=device,
                                            data_parameter=data_parameter,
                                            value=value)
        return self.post_with_tiedie_response("/data/attribute/write",
                                              tiedie_request, ValueResponse)

    def subscribe(self, device: Device, data_parameter: DataParameter) -> TiedieResponse[None]:
        """ Subscribes to a data stream topic for an IoT device.

        Args:
            device (Device): The device to subscribe to.
            data_parameter (DataParameter): The data parameter to subscribe to.

        Returns:
            TiedieResponse[None]: The response object containing the status of the request.
        """
        tiedie_request = TiedieReadRequest(device=device,
                                           data_parameter=data_parameter)
        return self.post_with_tiedie_response("/data/attribute/subscription/start",
                                              tiedie_request, None)

    def unsubscribe(self, device: Device, data_parameter: DataParameter) -> TiedieResponse[None]:
        """ Unsubscribes from a data stream topic for an IoT device.

        Args:
            device (Device): The device to unsubscribe from.
            data_parameter (DataParameter): The data parameter to unsubscribe from.

        Returns:
            TiedieResponse[None]: The response object containing the status of the request.
        """
        tiedie_request = TiedieReadRequest(device=device,
                                           data_parameter=data_parameter)
        return self.post_with_tiedie_response("/data/attribute/subscription/stop",
                                                tiedie_request, None)

    def register_topic(self,
                       topic: str,
                       device: Optional[Device] = None,
                       options: Optional[RegistrationOptions] = None) -> TiedieResponse[None]:
        """ Registers a data stream topic for IoT devices.

        Args:
            topic (str): The topic to register.
            device (Optional[Device], optional): The device to register a topic for. 
                Defaults to None.
            options (Optional[RegistrationOptions], optional): Additional topic registration 
                objects. Defaults to None.

        Returns:
            TiedieResponse[None]: The response object containing the status of the request.
        """
        tiedie_request = \
            TiedieRegisterTopicRequest(
                topic=topic, device=device, registration_options=options)
        return self.post_with_tiedie_response("/registration/topic",
                                              tiedie_request, None)

    def unregister_topic(self, topic: str):
        """ Unregisters a data stream topic for IoT devices.

        Args:
            topic (str): The topic to unregister.

        Returns:
            _type_: The response object containing the status of the request.
        """
        return self.delete_with_tiedie_response("/registration/topic",
                                                TopicQuery(topic=topic), None)
