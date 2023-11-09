#!python
# Copyright (c) 2023, Cisco and/or its affiliates.
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
        """Onboard a new device on the controller."""
        return self.post("/Devices", device, Device)

    def get_device(self, device_id: str):
        """Get the Device object using its unique ID."""
        return self.get(f"/Devices/{device_id}", Device)

    def get_devices(self):
        """Get a list of Device objects."""
        return self.get("/Devices", ListResponse[Device])

    def delete_device(self, device_id: str):
        """Un-onboard a device on the controller."""
        return self.delete(f"/Devices/{device_id}", None)

    def get_endpoint_apps(self):
        """Get a list of EndpointApp objects."""
        return self.get("/EndpointApps", ListResponse[EndpointApp])

    def get_endpoint_app(self, app_id: str):
        """Get the EndpointApp object using its unique ID."""
        return self.get(f"/EndpointApps/{app_id}", EndpointApp)

    def create_endpoint_app(self, endpoint_app: EndpointApp):
        """Create a new EndpointApp object."""
        return self.post("/EndpointApps", endpoint_app, EndpointApp)
