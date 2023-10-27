#!python
# Copyright (c) 2023, Cisco Systems, Inc. and/or its affiliates.
# All rights reserved.
# See LICENSE file in this distribution.
# SPDX-License-Identifier: Apache-2.0

from typing import List
from .auth import Authenticator
from .httpclient import AbstractHttpClient, HttpResponse
from tiedie_pylib.models import *


from typing import List
from .auth import Authenticator
from .httpclient import AbstractHttpClient, HttpResponse
from ..models import *


class OnboardingClient(AbstractHttpClient):
    """A class used to communicate with the TieDie onboarding SCIM APIs."""
    def __init__(self, base_url, authenticator):
        super().__init__(base_url, "application/scim+json", authenticator)


    def createDevice(self, device):
        """Onboard a new device on the controller."""
        return self.post("/Devices", device, Device)
    

    def getDevice(self, device_id, onb_app):
        """Get the Device object using its unique ID."""
        return self.get(f"/Devices/{device_id}/", Device, params={"onboardApp": onb_app})
    

    def deleteDevice(self, device_id, onb_app):
        """Un-onboard a device on the controller."""
        return self.delete(f"/Devices/{device_id}", None, params={"onboardApp": onb_app})
    