#!python
# Copyright (c) 2023, Cisco Systems, Inc. and/or its affiliates.
# All rights reserved.
# See LICENSE file in this distribution.
# SPDX-License-Identifier: Apache-2.0

""" this module defines onboarding a client """


from typing import List
from .auth import Authenticator
from .httpclient import AbstractHttpClient, HttpResponse
from tiedie.models import *


class OnboardingClient(AbstractHttpClient):
    """A class used to communicate with the TieDie onboarding SCIM APIs."""
    def __init__(self, base_url, authenticator):
        super().__init__(base_url, "application/scim+json", authenticator)


    def createDevice(self, device):
        """Onboard a new device on the controller."""
        return self.post("/Devices", device, Device)
    

    def getDevice(self, device_id):
        """Get the Device object using its unique ID."""
        return self.get(f"/Devices/{device_id}", Device)
    

    def getDevices(self):
        """Get a list of Device objects."""
        response = self.get("/Devices", ListResponse)
        return [Device.create(resource) for resource in response.body["Resources"]]
    

    def deleteDevice(self, device_id):
        """Un-onboard a device on the controller."""
        return self.delete(f"/Devices/{device_id}", None)
    
    
    def getEndpointApps(self):
        """Get a list of EndpointApp objects."""
        httpResponse = self.get("/EndpointApps", EndpointAppListResponse)
        return httpResponse
    

    def getEndpointApp(self, id: str):
        """Get the EndpointApp object using its unique ID."""
        return self.get(f"/EndpointApps/{id}", EndpointApp)
    

    def createEndpointApp(self, endpointApp: EndpointApp):
        """Create a new EndpointApp object."""
        return self.post("/EndpointApps", endpointApp, EndpointApp)
