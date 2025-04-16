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

from typing import List, Optional, Sequence

import urllib.parse as url_parse

from pydantic import RootModel

from tiedie.models.ble import DataParameter
from tiedie.models.requests import (
    BleConnectProtocolMap,
    BleConnectRequest,
    PropertyWriteRequest,
    SdfModel,
    TiedieConnectRequest,
    TiedieReadRequest,
    TiedieWriteRequest
)
from tiedie.models.responses import (
    BleDiscoverResponse, 
    ModelRegistrationResponse,
    PropertyResponse,
    TiedieDeviceResponse, 
    TiedieResponse, 
    ValueResponse,
    DataAppRegistration
)
from tiedie.models.scim import Device

from .auth import Authenticator
from .http_client import AbstractHttpClient


class ControlClient(AbstractHttpClient):
    """ Performs IoT device control and data management operations. """

    def __init__(self, base_url: str, authenticator: Authenticator):
        super().__init__(base_url, "application/json", authenticator)
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
            protocol_map=BleConnectProtocolMap(ble=request),
            retries=retries,
            retry_multiple_aps=retry_multiple_aps)

        ble_discover_response = self.post_with_tiedie_response(
            f'/{device.device_id}/action/connection', tiedie_request, BleDiscoverResponse)

        tiedie_response = TiedieResponse[Optional[Sequence[DataParameter]]](
            http=ble_discover_response.http,
            status=ble_discover_response.status,
            reason=ble_discover_response.reason,
            error_code=ble_discover_response.error_code,
        )
        if isinstance(ble_discover_response.body, BleDiscoverResponse) and \
                ble_discover_response.body.protocol_map is not None and \
                ble_discover_response.body.protocol_map != []:
            parameter_list = ble_discover_response.body.to_parameter_list(
                device.device_id)
            tiedie_response.body = parameter_list

        return tiedie_response

    def disconnect(self, device: Device):
        """ Disconnects from a connected IoT device. """
        return self.delete_with_tiedie_response(f'/{device.device_id}/action/connection',
                                                None, TiedieDeviceResponse)

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
            protocol_map=BleConnectProtocolMap(ble=request), retries=retries, retry_multiple_aps=retry_multiple_aps)

        ble_discover_response = self.put_with_tiedie_response(
        f'/{device.device_id}/action/connection', tiedie_request, BleDiscoverResponse)
        tiedie_response = TiedieResponse[Optional[Sequence[DataParameter]]](
            http=ble_discover_response.http,
            status=ble_discover_response.status,
            reason=ble_discover_response.reason,
            error_code=ble_discover_response.error_code,
        )
        if isinstance(ble_discover_response.body, BleDiscoverResponse) and \
                ble_discover_response.body.protocol_map is not None and \
                ble_discover_response.body.protocol_map != []:
            parameter_list = ble_discover_response.body.to_parameter_list(
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
            TiedieReadRequest(data_parameter=data_parameter)
        return self.post_with_tiedie_response(f"{device.device_id}/action/property/read",
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
        tiedie_request = TiedieWriteRequest(data_parameter=data_parameter,
                                            value=value)
        return self.post_with_tiedie_response(f"{device.device_id}/action/property/write",
                                              tiedie_request, ValueResponse)

    def read_property(self, device: str, sdf_ref: str) -> TiedieResponse[Optional[PropertyResponse]]:
        """ Reads a property from a device.

        Args:
            device (str): The device to read from.
            sdf_ref (str): The SDF reference of an SDF property to read.

        Returns:
            TiedieResponse[PropertyResponse]: The response object containing
              the value of the property.
        """
        encoded_sdf_ref = url_parse.quote(sdf_ref, safe='')
        return self.get_with_tiedie_response(f"/{device}/property/{encoded_sdf_ref}",
                                             None,
                                             PropertyResponse)

    def write_property(self, device: str, sdf_ref: str, value: bytes) -> TiedieResponse[Optional[PropertyResponse]]:
        """ Writes a property to a device.

        Args:
            device (str): The device to write to.
            sdf_ref (str): The SDF reference of an SDF property to write.
            value (str): The value to write in bytes.

        Returns:
            TiedieResponse[PropertyResponse]: The response object containing 
            the value of the property.
        """
        encoded_sdf_ref = url_parse.quote(sdf_ref, safe='')
        return self.put_with_tiedie_response(f"/{device}/property/{encoded_sdf_ref}",
                                              PropertyWriteRequest(value=value),
                                              PropertyResponse)


    def register_sdf_model(self, model: SdfModel):
        """ Registers a SDF model for an IoT device.

        Args:
            device (Device): The device to register the model for.
            model (str): The SDF model to register.

        Returns:
            HttpResponse[ModelRegistrationResponse]: The response object containing 
                the status of the request.
        """
        return self.post_with_tiedie_response("/registration/model",
                                              model, ModelRegistrationResponse)

    def update_sdf_model(self, sdf_ref: str, model: SdfModel):
        """ Updates a SDF model for an IoT device.

        Args:
            device (Device): The device to update the model for.
            model (str): The SDF model to update.

        Returns:
            HttpResponse[ModelRegistrationResponse]: The response object containing 
                the status of the request.
        """
        return self.put_with_tiedie_response(f"/registration/model/{sdf_ref}",
                                              model, ModelRegistrationResponse)


    def get_sdf_models(self):
        """ Retrieves the SDF models registered for an IoT device.

        Args:
            device (Device): The device to retrieve the models for.

        Returns:
            HttpResponse[ModelRegistrationResponse]: The response object containing 
                the status of the request.
        """
        return self.get("/registration/model",
                            RootModel[List[ModelRegistrationResponse]])

    def get_sdf_model(self, sdf_ref: str):
        """ Retrieves the SDF model registered for an IoT device.

        Args:
            device (Device): The device to retrieve the model for.
            model (str): The SDF model to retrieve.

        Returns:
            HttpResponse[ModelRegistrationResponse]: The response object containing 
                the status of the request.
        """
        encoded_sdf_ref = url_parse.quote(sdf_ref, safe='')
        return self.get(f"/registration/model/{encoded_sdf_ref}", SdfModel)

    def unregister_sdf_model(self, sdf_ref: str):
        """ Unregisters a SDF model for an IoT device.

        Args:
            device (Device): The device to unregister the model for.
            model (str): The SDF model to unregister.

        Returns:
            HttpResponse[ModelRegistrationResponse]: The response object containing 
                the status of the request.
        """
        encoded_sdf_ref = url_parse.quote(sdf_ref, safe='')
        return self.delete_with_tiedie_response(f"/registration/model/{encoded_sdf_ref}",
                                                None, ModelRegistrationResponse)

    def get_data_app(self, data_app_id: str):
        """ Retrieves the data app for an IoT device.

        Args:
            device (Device): The device to retrieve the data app for.

        Returns:
            HttpResponse[ModelRegistrationResponse]: The response object containing 
                the status of the request.
        """
        return self.get(f"/registration/data-app/{data_app_id}", DataAppRegistration)

    def create_data_app(self, data_app_id: str, data_app: DataAppRegistration):
        """ Creates a data app for an IoT device.

        Args:
            device (Device): The device to create the data app for.

        Returns:
            HttpResponse[ModelRegistrationResponse]: The response object containing 
                the status of the request.
        """
        return self.post_with_tiedie_response(f"/registration/data-app/{data_app_id}",
                                              data_app, DataAppRegistration)

    def update_data_app(self, data_app_id: str, data_app: DataAppRegistration):
        """ Updates a data app for an IoT device.

        Args:
            device (Device): The device to update the data app for.

        Returns:
            HttpResponse[ModelRegistrationResponse]: The response object containing 
                the status of the request.
        """
        return self.put_with_tiedie_response(f"/registration/data-app/{data_app_id}",
                                              data_app, DataAppRegistration)

    def delete_data_app(self, data_app_id: str):
        """ Deletes a data app for an IoT device.

        Args:
            device (Device): The device to delete the data app for.

        Returns:
            HttpResponse[ModelRegistrationResponse]: The response object containing 
                the status of the request.
        """
        return self.delete_with_tiedie_response(f"/registration/data-app/{data_app_id}",
                                                None, DataAppRegistration)
