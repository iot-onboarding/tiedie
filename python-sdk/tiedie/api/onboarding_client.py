#!python
# Copyright (c) 2023, Cisco Systems, Inc. and/or its affiliates.
# All rights reserved.
# See LICENSE file in this distribution.
# SPDX-License-Identifier: Apache-2.0

""" this module defines onboarding a client """


from tiedie.api.auth import Authenticator
from tiedie.models import Device, EndpointApp, ListResponse

from .http_client import AbstractHttpClient, HttpResponse


class OnboardingClient(AbstractHttpClient):
    """A class used to communicate with the TieDie onboarding SCIM APIs."""

    def __init__(self, base_url: str, authenticator: Authenticator):
        super().__init__(base_url, "application/scim+json", authenticator)

    def create_device(self, device: Device) -> HttpResponse[Device | None]:
        """Onboard a new device.

        Args:
            device (Device): Device object to be onboarded.

        Returns:
            HttpResponse[Device | None]: Response object containing the Device object.
        """
        return self.post("/Devices", device, Device)

    def get_device(self, device_id: str) -> HttpResponse[Device | None]:
        """Get the Device object using its unique ID.

        Args:
            device_id (str): Unique ID of the device.

        Returns:
            HttpResponse[Device | None]: Response object containing the Device object.
        """
        return self.get(f"/Devices/{device_id}", Device)

    def get_devices(self) -> HttpResponse[ListResponse[Device] | None]:
        """Get a list of Device objects.

        Returns:
            HttpResponse[ListResponse[Device] | None]: Response object containing 
                the list of Device objects.
        """
        return self.get("/Devices", ListResponse[Device])

    def delete_device(self, device_id: str) -> HttpResponse[None]:
        """Delete a device.

        Args:
            device_id (str): Unique ID of the device.

        Returns:
            HttpResponse[None]: Response object.
        """
        return self.delete(f"/Devices/{device_id}", None)

    def get_endpoint_apps(self) -> HttpResponse[ListResponse[EndpointApp] | None]:
        """Get a list of EndpointApp objects.

        Returns:
            HttpResponse[ListResponse[EndpointApp] | None]: Response object containing 
                the list of EndpointApp objects.
        """
        return self.get("/EndpointApps", ListResponse[EndpointApp])

    def get_endpoint_app(self, app_id: str) -> HttpResponse[EndpointApp | None]:
        """Get the EndpointApp object using its unique ID.

        Args:
            app_id (str): Unique ID of the EndpointApp.

        Returns:
            HttpResponse[EndpointApp | None]: Response object containing the EndpointApp object.
        """
        return self.get(f"/EndpointApps/{app_id}", EndpointApp)

    def create_endpoint_app(self, endpoint_app: EndpointApp) -> HttpResponse[EndpointApp | None]:
        """Onboard a new Endpoint application.

        Args:
            endpoint_app (EndpointApp): EndpointApp object to be created.

        Returns:
            HttpResponse[EndpointApp | None]: Response object containing the EndpointApp object.
        """
        return self.post("/EndpointApps", endpoint_app, EndpointApp)
