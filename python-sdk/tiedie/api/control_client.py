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
    TiedieWriteRequest,
    PropertyProtocolMap,
    BlePropertyProtocolMap,
)
from tiedie.models.responses import (
    BleDiscoverResponse,
    ModelRegistrationResponse,
    PropertyResponse,
    TiedieDeviceResponse,
    TiedieEventResponse,
    TiedieEventsResponse,
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
            detail=ble_discover_response.detail,
            nipc_status=ble_discover_response.nipc_status,
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

    def get_connection(self, device: Device) -> TiedieResponse[Optional[Sequence[DataParameter]]]:
        """ Retrieves the connection status of an IoT device.

        Args:
            device (Device): The device to retrieve the connection status for.

        Returns:
            TiedieResponse[Optional[Sequence[DataParameter]]]: The `TieDieResponse` object contains
            the state of the request. 
            A list of DataParameter objects is present if the service discovery was successful.
        """
        if device.device_id is None:
            raise ValueError("Device ID is required for connection")

        ble_discover_response = self.get_with_tiedie_response(f'/{device.device_id}/action/connection',
                                             None, BleDiscoverResponse)

        tiedie_response = TiedieResponse[Optional[Sequence[DataParameter]]](
            http=ble_discover_response.http,
            status=ble_discover_response.status,
            detail=ble_discover_response.detail,
            nipc_status=ble_discover_response.nipc_status,
        )
        if isinstance(ble_discover_response.body, BleDiscoverResponse) and \
                ble_discover_response.body.protocol_map is not None and \
                ble_discover_response.body.protocol_map != []:
            parameter_list = ble_discover_response.body.to_parameter_list(
                device.device_id)
            tiedie_response.body = parameter_list

        return tiedie_response

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
            detail=ble_discover_response.detail,
            nipc_status=ble_discover_response.nipc_status,
        )
        if isinstance(ble_discover_response.body, BleDiscoverResponse) and \
                ble_discover_response.body.protocol_map is not None and \
                ble_discover_response.body.protocol_map != []:
            parameter_list = ble_discover_response.body.to_parameter_list(
                device.device_id)
            tiedie_response.body = parameter_list

        return tiedie_response

    def read(self, device: Device, service_id: str, characteristic_id: str) \
            -> TiedieResponse[Optional[ValueResponse]]:
        """ Reads a value from a GATT characteristic of an IoT device.

        Args:
            device (Device): The device to read from.
            service_id (str): The service ID of the GATT characteristic.
            characteristic_id (str): The characteristic ID of the GATT
                characteristic.

        Returns:
            ValueResponse: The response object containing the value.
        """
        tiedie_request = \
            TiedieReadRequest(protocol_map=PropertyProtocolMap(
                ble=BlePropertyProtocolMap(
                    service_id=service_id,
                    characteristic_id=characteristic_id)))
        return self.post_with_tiedie_response(f"/{device.device_id}/action/property/read",
                                              tiedie_request, ValueResponse)

    def write(self, device: Device,
              service_id: str, 
              characteristic_id: str,
              value: str) -> TiedieResponse[Optional[ValueResponse]]:
        """ Writes a value to a GATT characteristic of an IoT device.

        Args:
            device (Device): The device to write to.
            service_id (str): The service ID of the GATT characteristic.
            characteristic_id (str): The characteristic ID of the GATT
                characteristic.
            value (str): The value to write.

        Returns:
            ValueResponse: The response object containing the value.
        """
        tiedie_request = TiedieWriteRequest(protocol_map=PropertyProtocolMap(
                ble=BlePropertyProtocolMap(
                    service_id=service_id,
                    characteristic_id=characteristic_id)),
                                            value=value)
        return self.post_with_tiedie_response(f"/{device.device_id}/action/property/write",
                                              tiedie_request, ValueResponse)

    def read_property(self, device: str, sdf_name: str) -> TiedieResponse[Optional[PropertyResponse]]:
        """ Reads a property from a device.

        Args:
            device (str): The device to read from.
            sdf_name (str): The SDF reference of an SDF property to read.

        Returns:
            TiedieResponse[PropertyResponse]: The response object containing
              the value of the property.
        """
        encoded_sdf_name = url_parse.quote(sdf_name, safe='')
        return self.get_with_tiedie_response(f"/{device}/property/{encoded_sdf_name}",
                                             None,
                                             PropertyResponse)

    def write_property(self, device: str, sdf_name: str, value: bytes) -> TiedieResponse[Optional[PropertyResponse]]:
        """ Writes a property to a device.

        Args:
            device (str): The device to write to.
            sdf_name (str): The SDF reference of an SDF property to write.
            value (str): The value to write in bytes.

        Returns:
            TiedieResponse[PropertyResponse]: The response object containing 
            the value of the property.
        """
        encoded_sdf_name = url_parse.quote(sdf_name, safe='')
        return self.put_with_tiedie_response(f"/{device}/property/{encoded_sdf_name}",
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

    def update_sdf_model(self, sdf_name: str, model: SdfModel):
        """ Updates a SDF model for an IoT device.

        Args:
            device (Device): The device to update the model for.
            model (str): The SDF model to update.

        Returns:
            HttpResponse[ModelRegistrationResponse]: The response object containing 
                the status of the request.
        """
        return self.put_with_tiedie_response(f"/registration/model/{sdf_name}",
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

    def get_sdf_model(self, sdf_name: str):
        """ Retrieves the SDF model registered for an IoT device.

        Args:
            device (Device): The device to retrieve the model for.
            model (str): The SDF model to retrieve.

        Returns:
            HttpResponse[ModelRegistrationResponse]: The response object containing 
                the status of the request.
        """
        encoded_sdf_name = url_parse.quote(sdf_name, safe='')
        return self.get(f"/registration/model/{encoded_sdf_name}", SdfModel)

    def unregister_sdf_model(self, sdf_name: str):
        """ Unregisters a SDF model for an IoT device.

        Args:
            device (Device): The device to unregister the model for.
            model (str): The SDF model to unregister.

        Returns:
            HttpResponse[ModelRegistrationResponse]: The response object containing 
                the status of the request.
        """
        encoded_sdf_name = url_parse.quote(sdf_name, safe='')
        return self.delete_with_tiedie_response(f"/registration/model/{encoded_sdf_name}",
                                                None, ModelRegistrationResponse)

    def get_data_app(self, data_app_id: str):
        """ Retrieves the data app for an IoT device.

        Args:
            device (Device): The device to retrieve the data app for.

        Returns:
            HttpResponse[ModelRegistrationResponse]: The response object containing 
                the status of the request.
        """
        return self.get_with_tiedie_response(f"/registration/data-app/{data_app_id}", None, DataAppRegistration)

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

    def enable_event(self, device_id: str, event: str) -> TiedieResponse[Optional[TiedieEventResponse]]:
        """Enable event reporting for a specific device and event.

        Args:
            device_id (str): The unique identifier of the device.
            event (str): The event name to enable.

        Returns:
            TiedieResponse[Optional[TiedieEventResponse]]: Response object.
        """
        encoded_sdf_name = url_parse.quote(event, safe='')
        return self.post_with_tiedie_response(f"/{device_id}/event/{encoded_sdf_name}", None, TiedieEventResponse)

    def disable_event(self, device_id: str, event: str) -> TiedieResponse[Optional[TiedieEventResponse]]:
        """Disable event reporting for a specific device and event.

        Args:
            device_id (str): The unique identifier of the device.
            event (str): The event name to disable.

        Returns:
            TiedieResponse[Optional[TiedieEventResponse]]: Response object.
        """
        encoded_sdf_name = url_parse.quote(event, safe='')
        return self.delete_with_tiedie_response(f"/{device_id}/event/{encoded_sdf_name}", None, TiedieEventResponse)

    def get_event(self, device_id: str, event: str) -> TiedieResponse[Optional[TiedieEventResponse]]:
        """Retrieve the status of a specific event for a device.

        Args:
            device_id (str): The unique identifier of the device.
            event (str): The event name to check.

        Returns:
            TiedieResponse[Optional[TiedieEventResponse]]: Response object.
        """
        encoded_sdf_name = url_parse.quote(event, safe='')
        return self.get_with_tiedie_response(f"/{device_id}/event/{encoded_sdf_name}", None, TiedieEventResponse)

    def get_all_events(self, device_id: str) -> TiedieResponse[Optional[TiedieEventsResponse]]:
        """Retrieve the status of all events for a device.

        Args:
            device_id (str): The unique identifier of the device.

        Returns:
            TiedieResponse[Optional[List[TiedieEventResponse]]]: Response object.
        """
        return self.get_with_tiedie_response(f"/{device_id}/event", None, TiedieEventsResponse)
