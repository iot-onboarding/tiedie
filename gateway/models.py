# Copyright (c) 2023-2024, Cisco Systems, Inc. and/or its affiliates.
# All rights reserved.
# See LICENSE file in this distribution.
# SPDX-License-Identifier: Apache-2.0

"""
This script defines SQLAlchemy models for database interactions,
representing devices, and endpoint applications for a web application.
"""

from datetime import datetime
from typing import List, Optional

import uuid
from sqlalchemy import Boolean, Column, DateTime, \
    ForeignKey, String, ARRAY
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, relationship, mapped_column
from config import EXTERNAL_HOST, EXTERNAL_PORT, MQTT_PORT
from scim_extensions import scim_ext_read
from database import db


devices_endpoint_apps = db.Table(
    "devices_endpoint_apps",
    Column("endpoint_app_id", UUID(as_uuid=True),
           ForeignKey("endpoint_app.id"), primary_key=True),
    Column(
        "device_id", UUID(as_uuid=True), ForeignKey("devices.device_id"), primary_key=True
    ),
)


class Device(db.Model):
    """ Core elements of Tiedie devices."""
    __tablename__ = "devices"
    device_id = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    schemas = mapped_column(ARRAY(String))
    display_name = mapped_column(String)
    active = mapped_column(Boolean)
    created_time = mapped_column(String)
    modified_time = mapped_column(String)

    endpoint_apps: Mapped[List["EndpointApp"]] = relationship(
        "EndpointApp", secondary=devices_endpoint_apps)
    ble_extension: Mapped[Optional["BleExtension"]] = relationship(back_populates="device")
    ethermab_extension: Mapped[Optional["EtherMABExtension"]] =  relationship(
        back_populates="device")
    fdo_extension: Mapped[Optional["FDOExtension"]] = relationship(back_populates="device")

    def __init__(
            self,
            schemas,
            display_name,
            active,
            endpoint_apps,
            created_time
    ):

        self.schemas = schemas
        self.display_name = display_name
        self.active = active
        if endpoint_apps:
            self.endpoint_apps.extend(endpoint_apps)
        self.created_time = created_time
        self.modified_time = created_time


    def serialize(self):
        """serialize function"""
        response = {
            "schemas" : self.schemas,
            "id": self.device_id,
            "displayName": self.display_name,
            "active": self.active,
            "meta": {"resourceType": "Device",
                     "created": self.created_time,
                     "lastModified": self.modified_time},
            }
        for read_fn in scim_ext_read:
            read_fn(self, response)

        if self.endpoint_apps:
            response["urn:ietf:params:scim:schemas:extension:endpointAppsExt:2.0:Device"] = \
                {
                "applications": [{"value": app.id,
                                  "$ref":  f"https://{EXTERNAL_HOST}:"
                                  f"{EXTERNAL_PORT}/scim/v2/EndpointApps/"
                                  f"{app.id}"
                                  } for app in self.endpoint_apps],
                "deviceControlEnterpriseEndpoint":
                    f"https://{EXTERNAL_HOST}:"
                    f"{EXTERNAL_PORT}/control",
                "telemetryEnterpriseEndpoint":
                    f"ssl://{EXTERNAL_HOST}:{MQTT_PORT}",
            }
        return response

class EndpointApp(db.Model):
    """ Store information about applications linked to BLE devices. """
    __tablename__ = "endpoint_app"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    applicationType: Mapped[str] = mapped_column(String())
    applicationName: Mapped[str] = mapped_column(
        String(), unique=True, nullable=False)
    rootPublicKey: Mapped[Optional[str]] = mapped_column(String())
    subjectName: Mapped[Optional[str]] = mapped_column(String())
    clientToken: Mapped[Optional[UUID]] = mapped_column(String())
    createdTime: Mapped[datetime] = mapped_column(DateTime())
    modifiedTime: Mapped[datetime] = mapped_column(DateTime())
    password: Mapped[Optional[str]] = mapped_column(String())
    is_admin: Mapped[bool] = mapped_column(Boolean(), default=False)

    def __repr__(self):
        return f"<id {self.id}>"

    def serialize(self):
        """ Serialize function """
        certificateInfo = None

        if self.rootPublicKey:
            certificateInfo = {
                "rootPublicKey": self.rootPublicKey,
                "subjectName": self.subjectName
            }

        return {
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:EndpointApp"],
            "id": self.id,
            "applicationType": self.applicationType,
            "applicationName": self.applicationName,
            "certificateInfo": certificateInfo,
            "clientToken": str(self.clientToken) if self.clientToken else None,
            "meta": {
                "resourceType": "EndpointApp",
                "created": self.createdTime,
                "lastModified": self.modifiedTime,
                "location": f"https://{EXTERNAL_HOST}:{EXTERNAL_PORT}/scim/v2/EndpointApp/{self.id}"
            }
        }


class OnboardingAppKey(db.Model):
    """ Store keys for onboarding applications. """
    __tablename__ = "onboardingapi_key"

    key_type = Column(String(), primary_key=True, unique=True)
    key_val = Column(String(), primary_key=True, unique=True)

    def __init__(self, key_type, key_val):
        self.key_type = key_type
        self.key_val = key_val
