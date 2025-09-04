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

from typing import List, Optional, Sequence, Union

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
    ProblemDetails,
    PropertyResponse,
    PropertyWriteResponse,
    TiedieDeviceResponse,
    TiedieEventResponse,
    NipcResponse,
    ValueResponse,
    DataAppRegistration
)
from tiedie.models.scim import Device

from .auth import Authenticator
from .http_client import AbstractHttpClient


class ControlClient(AbstractHttpClient):
    """ Performs IoT device control and data management operations. """

    def __init__(self, base_url: str, authenticator: Authenticator):
        super().__init__(base_url, "application/nipc+json", authenticator)
        self.base_url = base_url
        self.authenticator = authenticator

    def connect(self, device: Device,
                request: BleConnectRequest = BleConnectRequest(),
                retries=3,
                retry_multiple_aps=True) \
            -> NipcResponse[Optional[Sequence[DataParameter]]]:
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
            sdf_protocol_map=BleConnectProtocolMap(ble=request),
            retries=retries,
            retry_multiple_aps=retry_multiple_aps)

        ble_discover_response = self.post_with_nipc_response(
            f'/devices/{device.device_id}/connections', tiedie_request, BleDiscoverResponse)

        # Handle success case: extract parameter list from BLE discovery response
        if (ble_discover_response.is_success and
                isinstance(ble_discover_response.body, BleDiscoverResponse)):
            sdf_protocol_map = ble_discover_response.body.sdf_protocol_map
            if sdf_protocol_map is not None and sdf_protocol_map != []:
                parameter_list = ble_discover_response.body.to_parameter_list(device.device_id)
                return NipcResponse[Optional[Sequence[DataParameter]]](
                    http=ble_discover_response.http,
                    body=parameter_list
                )

        # Handle error case or empty response
        return NipcResponse[Optional[Sequence[DataParameter]]](
            http=ble_discover_response.http,
            error=ble_discover_response.error,
            body=None
        )

    def disconnect(self, device: Device) -> NipcResponse[Optional[TiedieDeviceResponse]]:
        """ Disconnects from a connected IoT device. """
        return self.delete_with_nipc_response(f'/devices/{device.device_id}/connections',
                                             None, TiedieDeviceResponse)

    def get_connection(self, device: Device) -> NipcResponse[Optional[Sequence[DataParameter]]]:
        """ Retrieves the connection status of an IoT device.

        Args:
            device (Device): The device to retrieve the connection status for.

        Returns:
            NipcResponse[Optional[Sequence[DataParameter]]]: The NIPC response object contains
            the state of the request.
            A list of DataParameter objects is present if the service discovery was successful.
        """
        if device.device_id is None:
            raise ValueError("Device ID is required for connection")

        ble_discover_response = self.get_with_nipc_response(
            f'/devices/{device.device_id}/connections',
            None, BleDiscoverResponse
        )

        # Handle success case: extract parameter list from BLE discovery response
        if (ble_discover_response.is_success and
                isinstance(ble_discover_response.body, BleDiscoverResponse)):
            sdf_protocol_map = ble_discover_response.body.sdf_protocol_map
            if sdf_protocol_map is not None and sdf_protocol_map != []:
                parameter_list = ble_discover_response.body.to_parameter_list(device.device_id)
                return NipcResponse[Optional[Sequence[DataParameter]]](
                    http=ble_discover_response.http,
                    body=parameter_list
                )

        # Handle error case or empty response
        return NipcResponse[Optional[Sequence[DataParameter]]](
            http=ble_discover_response.http,
            error=ble_discover_response.error,
            body=None
        )

    def discover(self, device: Device,
                 request=BleConnectRequest(),
                 retries=3,
                 retry_multiple_aps=True) \
            -> NipcResponse[Optional[Sequence[DataParameter]]]:
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
            NipcResponse[Optional[Sequence[DataParameter]]]: The NIPC response object contains
            the state of the request.
            A list of DataParameter objects is present if the service discovery was successful.
        """
        if device.device_id is None:
            raise ValueError("Device ID is required for connection")

        tiedie_request = TiedieConnectRequest(
            sdf_protocol_map=BleConnectProtocolMap(ble=request),
            retries=retries,
            retry_multiple_aps=retry_multiple_aps
        )

        ble_discover_response = self.put_with_nipc_response(
            f'/devices/{device.device_id}/connections', tiedie_request, BleDiscoverResponse)

        # Handle success case: extract parameter list from BLE discovery response
        if ble_discover_response.is_success and \
            isinstance(ble_discover_response.body, BleDiscoverResponse):
            if ble_discover_response.body.sdf_protocol_map is not None and \
                ble_discover_response.body.sdf_protocol_map != []:
                parameter_list = ble_discover_response.body.to_parameter_list(device.device_id)
                return NipcResponse[Optional[Sequence[DataParameter]]](
                    http=ble_discover_response.http,
                    body=parameter_list
                )

        # Handle error case or empty response
        return NipcResponse[Optional[Sequence[DataParameter]]](
            http=ble_discover_response.http,
            error=ble_discover_response.error,
            body=None
        )

    def read(self, device: Device, service_id: str, characteristic_id: str) \
            -> NipcResponse[Optional[ValueResponse]]:
        """ Reads a value from a GATT characteristic of an IoT device.

        Args:
            device (Device): The device to read from.
            service_id (str): The service ID of the GATT characteristic.
            characteristic_id (str): The characteristic ID of the GATT
                characteristic.

        Returns:
            NipcResponse[Optional[ValueResponse]]: The NIPC response object containing the value.
        """
        tiedie_request = \
            TiedieReadRequest(sdf_protocol_map=PropertyProtocolMap(
                ble=BlePropertyProtocolMap(
                    service_id=service_id,
                    characteristic_id=characteristic_id)))
        return self.post_with_nipc_response(f"/extensions/{device.device_id}/properties/read",
                                           tiedie_request, ValueResponse)

    def write(self, device: Device,
              service_id: str,
              characteristic_id: str,
              value: str) -> NipcResponse[Optional[ValueResponse]]:
        """ Writes a value to a GATT characteristic of an IoT device.

        Args:
            device (Device): The device to write to.
            service_id (str): The service ID of the GATT characteristic.
            characteristic_id (str): The characteristic ID of the GATT
                characteristic.
            value (str): The value to write.

        Returns:
            NipcResponse[Optional[ValueResponse]]: The NIPC response object containing the value.
        """
        tiedie_request = TiedieWriteRequest(sdf_protocol_map=PropertyProtocolMap(
                ble=BlePropertyProtocolMap(
                    service_id=service_id,
                    characteristic_id=characteristic_id)),
                                            value=value)
        endpoint = f"/extensions/{device.device_id}/properties/write"
        return self.post_with_nipc_response(endpoint, tiedie_request, ValueResponse)

    def read_property(self,
                      device: str,
                      sdf_name: str) -> NipcResponse[
                          Optional[Union[PropertyResponse, ProblemDetails]]
                      ]:
        """ Reads a property from a device.

        Args:
            device (str): The device to read from.
            sdf_name (str): The SDF reference of an SDF property to read.

        Returns:
            NipcResponse[Optional[Union[PropertyResponse, ProblemDetails]]]:
                The NIPC response object containing the value of the property.
        """
        encoded_sdf_name = url_parse.quote(sdf_name)
        endpoint = f"/devices/{device}/properties?propertyName={encoded_sdf_name}"
        response_type = RootModel[List[Union[PropertyResponse, ProblemDetails]]]
        return self.get_with_nipc_response(endpoint, None, response_type)

    def write_property(self,
                        device: str,
                        sdf_name: str,
                        value: str) -> NipcResponse[
                            Optional[List[Union[PropertyWriteResponse, ProblemDetails]]]
                        ]:
        """ Writes a property to a device.

        Args:
            device (str): The device to write to.
            sdf_name (str): The SDF reference of an SDF property to write.
            value (str): The value to write in bytes.

        Returns:
            NipcResponse[Optional[List[Union[PropertyWriteResponse, ProblemDetails]]]]:
                The NIPC response object containing the value of the property.
        """
        return self.put_with_nipc_response(
            f"/devices/{device}/properties",
            [PropertyWriteRequest(property=sdf_name, value=value)],
            RootModel[List[Union[PropertyWriteResponse, ProblemDetails]]]
        )


    def register_sdf_model(self, model: SdfModel):
        """ Registers a SDF model for an IoT device.

        Args:
            device (Device): The device to register the model for.
            model (str): The SDF model to register.

        Returns:
            HttpResponse[ModelRegistrationResponse]: The response object containing
                the status of the request.
        """
        return self.post_with_nipc_response("/registrations/models",
                                              model, RootModel[List[ModelRegistrationResponse]],
                                              "application/sdf+json")

    def update_sdf_model(self, sdf_name: str, model: SdfModel):
        """ Updates a SDF model for an IoT device.

        Args:
            device (Device): The device to update the model for.
            model (str): The SDF model to update.

        Returns:
            HttpResponse[ModelRegistrationResponse]: The response object containing
                the status of the request.
        """
        encoded_sdf_name = url_parse.quote(sdf_name)
        return self.put_with_nipc_response(f"/registrations/models?sdfName={encoded_sdf_name}",
                                              model, ModelRegistrationResponse,
                                              "application/sdf+json")


    def get_sdf_models(self):
        """ Retrieves the SDF models registered for an IoT device.

        Args:
            device (Device): The device to retrieve the models for.

        Returns:
            HttpResponse[ModelRegistrationResponse]: The response object containing
                the status of the request.
        """
        return self.get("/registrations/models",
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
        encoded_sdf_name = url_parse.quote(sdf_name)
        return self.get(f"/registrations/models?sdfName={encoded_sdf_name}", SdfModel)

    def unregister_sdf_model(self, sdf_name: str):
        """ Unregisters a SDF model for an IoT device.

        Args:
            device (Device): The device to unregister the model for.
            model (str): The SDF model to unregister.

        Returns:
            HttpResponse[ModelRegistrationResponse]: The response object containing
                the status of the request.
        """
        encoded_sdf_name = url_parse.quote(sdf_name)
        return self.delete_with_nipc_response(f"/registrations/models?sdfName={encoded_sdf_name}",
                                                None, ModelRegistrationResponse)

    def get_data_app(self, data_app_id: str):
        """ Retrieves the data app for an IoT device.

        Args:
            device (Device): The device to retrieve the data app for.

        Returns:
            HttpResponse[ModelRegistrationResponse]: The response object containing
                the status of the request.
        """
        return self.get_with_nipc_response(
            f"/registrations/data-apps?dataAppId={data_app_id}",
            None,
            DataAppRegistration
        )

    def create_data_app(self, data_app_id: str, data_app: DataAppRegistration):
        """ Creates a data app for an IoT device.

        Args:
            device (Device): The device to create the data app for.

        Returns:
            HttpResponse[ModelRegistrationResponse]: The response object containing
                the status of the request.
        """
        return self.post_with_nipc_response(f"/registrations/data-apps?dataAppId={data_app_id}",
                                              data_app, DataAppRegistration)

    def update_data_app(self, data_app_id: str, data_app: DataAppRegistration):
        """ Updates a data app for an IoT device.

        Args:
            device (Device): The device to update the data app for.

        Returns:
            HttpResponse[ModelRegistrationResponse]: The response object containing
                the status of the request.
        """
        return self.put_with_nipc_response(f"/registrations/data-apps?dataAppId={data_app_id}",
                                              data_app, DataAppRegistration)

    def delete_data_app(self, data_app_id: str):
        """ Deletes a data app for an IoT device.

        Args:
            device (Device): The device to delete the data app for.

        Returns:
            HttpResponse[ModelRegistrationResponse]: The response object containing
                the status of the request.
        """
        return self.delete_with_nipc_response(f"/registrations/data-apps?dataAppId={data_app_id}",
                                                None, DataAppRegistration)

    def enable_event(self,
                     device_id: str,
                     event: str) -> NipcResponse[Optional[str]]:
        """Enable event reporting for a specific device and event.

        Args:
            device_id (str): The unique identifier of the device.
            event (str): The event name to enable.

        Returns:
            NipcResponse[Optional[str]]: NIPC response object.
        """
        encoded_sdf_name = url_parse.quote(event)
        resp = self.post_with_nipc_response(
            f"/devices/{device_id}/events?eventName={encoded_sdf_name}",
            None,
            None
        )
        resp.body = resp.http.headers.get('Location').split('?instanceId=')[1]
        return resp

    def disable_event(self,
                      device_id: str,
                      instance_id: str) -> NipcResponse[None]:
        """Disable event reporting for a specific device and event.

        Args:
            device_id (str): The unique identifier of the device.
            instance_id (str): The unique identifier of the event.

        Returns:
            NipcResponse[None]: NIPC response object.
        """
        return self.delete_with_nipc_response(
            f"/devices/{device_id}/events?instanceId={instance_id}",
            None,
            None)

    def get_event(self,
                  device_id: str,
                  instance_id: str) -> NipcResponse[Optional[List[TiedieEventResponse]]]:
        """Retrieve the status of a specific event for a device.

        Args:
            device_id (str): The unique identifier of the device.
            instance_id (str): The unique identifier of the event.

        Returns:
            NipcResponse[Optional[List[TiedieEventResponse]]]: NIPC response object.
        """
        return self.get_with_nipc_response(
            f"/devices/{device_id}/events?instanceId={instance_id}",
            None,
            RootModel[List[TiedieEventResponse]]
        )

    def get_all_events(
            self, device_id: str
    ) -> NipcResponse[Optional[List[TiedieEventResponse]]]:
        """Retrieve the status of all events for a device.

        Args:
            device_id (str): The unique identifier of the device.

        Returns:
            NipcResponse[Optional[List[TiedieEventResponse]]]: NIPC response object.
        """
        endpoint = f"/devices/{device_id}/events"
        response_type = RootModel[List[TiedieEventResponse]]
        return self.get_with_nipc_response(endpoint, None, response_type)
