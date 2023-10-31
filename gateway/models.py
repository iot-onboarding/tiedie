# Copyright (c) 2023, Cisco and/or its affiliates.
# All rights reserved.
# See LICENSE file in this distribution.
# SPDX-License-Identifier: Apache-2.0

"""

This script defines SQLAlchemy models for database interactions,
representing users, endpoint applications, topics, and filters for a
web application.

"""

from datetime import datetime
from typing import Any, List, Optional

import uuid
from sqlalchemy import JSON, Boolean, Column, DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, relationship, mapped_column
from config import EXTERNAL_HOST, EXTERNAL_PORT, MQTT_PORT
from database import db

gatt_topic_devices = db.Table(
    "gatt_topic_devices",
    Column(
        "topic", String(), db.ForeignKey("gatt_topics.topic"), primary_key=True
    ),
    Column(
        "device_id", UUID(as_uuid=True), db.ForeignKey("bledevices.id"), primary_key=True
    ),
)

adv_topic_devices = db.Table(
    "adv_topic_devices",
    Column(
        "topic", String(), db.ForeignKey("adv_topics.topic"), primary_key=True
    ),
    Column(
        "device_id", UUID(as_uuid=True), db.ForeignKey("bledevices.id"), primary_key=True
    ),
)


devices_endpoint_apps = db.Table(
    "devices_endpoint_apps",
    Column("endpoint_app_id", UUID(as_uuid=True),
           ForeignKey("endpoint_app.id"), primary_key=True),
    Column(
        "device_id", UUID(as_uuid=True), ForeignKey("bledevices.id"), primary_key=True
    ),
)


class User(db.Model):
    """ Represent BLE device information and associated data fields. """
    __tablename__ = "bledevices"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    schemas = db.Column(db.String())
    deviceDisplayName = db.Column(db.String())
    adminState = db.Column(db.Boolean())
    versionSupport = db.Column(db.ARRAY(db.String()))
    deviceMacAddress = db.Column(db.String())
    isRandom = db.Column(db.Boolean())
    separateBroadcastAddress = db.Column(db.ARRAY(db.String()))
    irk = db.Column(db.String())
    pairingMethods = db.Column(db.ARRAY(db.String()))
    pairingNull = db.Column(db.String())
    pairingJustWorksKeys = db.Column(db.Integer())
    pairingPassKey = db.Column(db.Integer())
    pairingOOBKey = db.Column(db.String())
    pairingOOBRN = db.Column(db.BigInteger())
    creTime = db.Column(db.String())
    modTime = db.Column(db.String())

    endpointApps: Mapped[List["EndpointApp"]] = relationship(
        "EndpointApp", secondary=devices_endpoint_apps)

    gatt_topics = relationship("GattTopic",
                               secondary=gatt_topic_devices, back_populates="devices")

    adv_topics = relationship("AdvTopic",
                              secondary=adv_topic_devices, back_populates="devices")

    def __init__(
        self,
        schemas,
        deviceDisplayName,
        adminState,
        versionSupport,
        deviceMacAddress,
        isRandom,
        separateBroadcastAddress,
        irk,
        pairingMethods,
        pairingNull,
        pairingJustWorksKeys,
        pairingPassKey,
        pairingOOBKey,
        pairingOOBRN,
        endpointApps,
        tCreated,
    ):
        self.schemas = schemas
        self.deviceDisplayName = deviceDisplayName
        self.adminState = adminState
        self.versionSupport = versionSupport
        self.deviceMacAddress = deviceMacAddress
        self.isRandom = isRandom
        self.separateBroadcastAddress = separateBroadcastAddress
        self.irk = irk
        self.pairingMethods = pairingMethods
        self.pairingNull = pairingNull
        self.pairingJustWorksKeys = pairingJustWorksKeys
        self.pairingPassKey = pairingPassKey
        self.pairingOOBKey = pairingOOBKey
        self.pairingOOBRN = pairingOOBRN
        if endpointApps:
            self.endpointApps.extend(endpointApps)
        self.creTime = tCreated
        self.modTime = tCreated

    def __repr__(self):
        return f"<id {self.id}>"

    def serialize(self):
        """serialize function"""
        response = {
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Device",
                        "urn:ietf:params:scim:schemas:extension:ble:2.0:Device"],
            "id": str(self.id),
            "deviceDisplayName": self.deviceDisplayName,
            "adminState": self.adminState,
            "urn:ietf:params:scim:schemas:extension:ble:2.0:Device": {
                "versionSupport": self.versionSupport,
                "deviceMacAddress": self.deviceMacAddress,
                "isRandom": self.isRandom,
                "pairingMethods": self.pairingMethods,
            },
            "meta": {"resourceType": "Device",
                     "created": self.creTime,
                     "lastModified": self.modTime},
        }

        if self.irk:
            response["urn:ietf:params:scim:schemas:extension:ble:2.0:Device"][
                "irk"] = self.irk
        if self.separateBroadcastAddress:
            response["urn:ietf:params:scim:schemas:extension:ble:2.0:Device"][
                "separateBroadcastAddress"] = self.separateBroadcastAddress

        if self.pairingNull:
            response["urn:ietf:params:scim:schemas:extension:ble:2.0:Device"][
                "urn:ietf:params:scim:schemas:extension:pairingNull:2.0:Device"] = self.pairingNull
        if self.pairingJustWorksKeys:
            response["urn:ietf:params:scim:schemas:extension:ble:2.0:Device"][
                "urn:ietf:params:scim:schemas:extension:pairingJustWorks:2.0:Device"] = {
                    "key": self.pairingJustWorksKeys
            }
        if self.pairingPassKey:
            response["urn:ietf:params:scim:schemas:extension:ble:2.0:Device"][
                "urn:ietf:params:scim:schemas:extension:pairingPassKey:2.0:Device"] = {
                    "key": self.pairingPassKey
            }
        if self.pairingOOBKey:
            response["urn:ietf:params:scim:schemas:extension:ble:2.0:Device"][
                "urn:ietf:params:scim:schemas:extension:pairingOOB:2.0:Device"] = {
                    "key": self.pairingOOBKey,
                    "randNumber": self.pairingOOBRN
            }

        if self.endpointApps is not None:
            response["schemas"].append(
                "urn:ietf:params:scim:schemas:extension:endpointAppsExt:2.0:Device")
            response["urn:ietf:params:scim:schemas:extension:endpointAppsExt:2.0:Device"] = {
                "onboardingUrl": f"https://{EXTERNAL_HOST}:{EXTERNAL_PORT}/scim/v2/EndpointApps/onboarding",
                "deviceControlUrl": f"https://{EXTERNAL_HOST}:{EXTERNAL_PORT}/control",
                "dataReceiverUrl": f"ssl://{EXTERNAL_HOST}:{MQTT_PORT}",
            }
        return response
    

class EndpointApp(db.Model):
    __tablename__ = "endpoint_app"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    applicationType: Mapped[str] = mapped_column(String())
    applicationName: Mapped[str] = mapped_column(
        String(), unique=True, nullable=False)
    certificateInfo: Mapped[Optional[dict]
                            ] = mapped_column(JSON(), nullable=True)
    clientToken: Mapped[Optional[UUID]] = mapped_column(String())
    createdTime: Mapped[datetime] = mapped_column(DateTime())
    modifiedTime: Mapped[datetime] = mapped_column(DateTime())
    password: Mapped[Optional[str]] = mapped_column(String())
    is_admin: Mapped[bool] = mapped_column(Boolean(), default=False)

    def __repr__(self):
        return f"<id {self.id}>"

    def serialize(self):
        """ Serialize function """
        return {
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:EndpointApp"],
            "id": str(self.id),
            "applicationType": self.applicationType,
            "applicationName": self.applicationName,
            "certificateInfo": self.certificateInfo,
            "clientToken": str(self.clientToken),
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

    keyType = Column(String(), primary_key=True, unique=True)
    keyVal = Column(String(), primary_key=True, unique=True)

    def __init__(self, keyType, keyVal):
        self.keyType = keyType
        self.keyVal = keyVal


class GattTopic(db.Model):
    """ Define topics for GATT services and their data formats. """
    __tablename__ = "gatt_topics"

    topic = Column(String(), primary_key=True, unique=True)
    service_uuid = Column(String())
    characteristic_uuid = Column(String())
    data_format = Column(Enum("default", "payload", name="data_format"))

    devices: Mapped[List[User]] = relationship(
        secondary=gatt_topic_devices, back_populates="gatt_topics")

    def __init__(self, topic, service_uuid, characteristic_uuid, data_format, devices):
        self.topic = topic
        self.service_uuid = service_uuid
        self.characteristic_uuid = characteristic_uuid
        self.data_format = data_format
        self.devices.extend(devices)

    def __repr__(self):
        return f"<topic {self.topic}>"


class AdvFilter(db.Model):
    """ Define filters for BLE advertisement topics. """
    __tablename__ = "adv_filters"

    id: Mapped[int] = mapped_column(primary_key=True)
    topic: Mapped[str] = mapped_column(ForeignKey(column="adv_topics.topic"))
    mac_filter = Column(String())
    ad_type_filter = Column(String())
    ad_data_filter = Column(String())

    def __init__(self, topic: str, mac_filter: str, ad_type_filter: str, ad_data_filter: str):
        self.topic = topic
        self.mac_filter = mac_filter
        self.ad_type_filter = ad_type_filter
        self.ad_data_filter = ad_data_filter

    def __repr__(self):
        return f"<id {self.id}>"


class AdvTopic(db.Model):
    """ Represent topics for BLE advertisement data. """
    __tablename__ = "adv_topics"

    topic = Column(String(), primary_key=True, unique=True)
    data_format = Column(Enum("default", "payload", name="data_format"))
    devices: Mapped[List[User]] = relationship(
        secondary=adv_topic_devices, back_populates="adv_topics")
    onboarded = Column(Boolean, default=False)
    filter_type = Column(String())
    filters: Mapped[List[AdvFilter]] = relationship()

    def __init__(self, topic, data_format, devices: Optional[Any] = None,
                 filter_type: Optional[String] = None,
                 filters: Optional[List[AdvFilter]] = None):
        self.topic = topic
        self.data_format = data_format
        if devices is not None:
            self.onboarded = True
            self.devices.extend(devices)
        if filters is not None:
            self.filter_type = filter_type
            self.filters.extend(filters)

    def __repr__(self):
        return "<topic {}>".format(self.topic)


class DataAppTopic(db.Model):
    """ Store topics associated with data applications. """
    __tablename__ = "data_app_topics"

    data_app_id = Column(String(), ForeignKey(
        "endpoint_app.applicationName"), primary_key=True)
    topic = Column(String(), primary_key=True)
    rw = Column(Integer)

    def __init__(self, data_app_id, topic):
        self.data_app_id = data_app_id
        self.topic = topic
        self.rw = 1

    def __repr__(self):
        return f"<data_app_id {self.data_app_id}>"
