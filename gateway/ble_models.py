# Copyright (c) 2024, Cisco Systems, Inc. and/or its affiliates.
# All rights reserved.
# See LICENSE file in this distribution.
# SPDX-License-Identifier: Apache-2.0

"""

This script defines SQLAlchemy models for BLE database interactions,
representing GATT topics, and filters for a web application.

"""

from typing import Any, List, Optional

from sqlalchemy import Boolean, Column, Enum, \
    ForeignKey, Integer, String, ARRAY, BigInteger
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, relationship, mapped_column
from database import db
from models import Device

gatt_topic_devices = db.Table(
    "gatt_topic_devices",
    Column(
        "topic", String(), db.ForeignKey("gatt_topics.topic"), primary_key=True
    ),
    Column(
        "device_id", UUID(as_uuid=True), db.ForeignKey("bledevices.device_id"), primary_key=True
    ),
)

adv_topic_devices = db.Table(
    "adv_topic_devices",
    Column(
        "topic", String(), db.ForeignKey("adv_topics.topic"), primary_key=True
    ),
    Column(
        "device_id", UUID(as_uuid=True), db.ForeignKey("bledevices.device_id"), primary_key=True
    ),
)

connection_topic_devices = db.Table(
    "connection_topic_devices",
    Column(
        "topic", String(), db.ForeignKey("connection_topics.topic"), primary_key=True
    ),
    Column(
        "device_id", UUID(as_uuid=True), db.ForeignKey("bledevices.device_id"), primary_key=True
    ),
)

class BleExtension(db.Model):
    """ Represent BLE device information and associated data fields. """
    __tablename__ = "bledevices"

    device_id = mapped_column(UUID(as_uuid=True),ForeignKey("devices.device_id"),
                              primary_key=True)
    device_mac_address = mapped_column(String)
    version_support = mapped_column(ARRAY(String))
    is_random = mapped_column(Boolean())
    separate_broadcast_address = mapped_column(ARRAY(String))
    irk = mapped_column(String)
    pairing_methods = mapped_column(ARRAY(String))
    pairing_null = mapped_column(String)
    pairing_just_works_key = mapped_column(Integer)
    pairing_pass_key = mapped_column(Integer)
    pairing_oob_key = mapped_column(String)
    pairing_oobrn = mapped_column(BigInteger)
    gatt_topics: Mapped[List["GattTopic"]] = \
        relationship("GattTopic", secondary=gatt_topic_devices,
                     back_populates="devices")
    adv_topics: Mapped[List["AdvTopic"]] = relationship("AdvTopic",
                              secondary=adv_topic_devices, back_populates="devices")

    connection_topics: Mapped[List["ConnectionTopic"]] = \
        relationship("ConnectionTopic", secondary=connection_topic_devices,
                     back_populates="devices")
    device: Mapped[Device] = relationship(back_populates="ble_extension")

    def __init__(
        self,
        device_id,
        device_mac_address,
        version_support,
        is_random,
        separate_broadcast_address,
        irk,
        pairing_methods,
        pairing_null,
        pairing_just_works_keys,
        pairing_pass_key,
        pairing_oob_key,
        pairing_oobrn,
    ):
        self.device_id = device_id
        self.device_mac_address = device_mac_address
        self.version_support = version_support
        self.is_random = is_random
        self.separate_broadcast_address = separate_broadcast_address
        self.irk = irk
        self.pairing_methods = pairing_methods
        self.pairing_null = pairing_null
        self.pairing_just_works_key = pairing_just_works_keys
        self.pairing_pass_key = pairing_pass_key
        self.pairing_oob_key = pairing_oob_key
        self.pairing_oobrn = pairing_oobrn

    def __repr__(self):
        return f"<id {self.device_id}>"

    def serialize(self):
        """serialize function"""
        ble_json = "urn:ietf:params:scim:schemas:extension:ble:2.0:Device"
        response = {
            ble_json : {
                "versionSupport": self.version_support,
                "deviceMacAddress": self.device_mac_address,
                "isRandom": self.is_random,
                "pairingMethods": self.pairing_methods,
            }
        }
        if self.irk:
            response[ble_json]["irk"] = self.irk
        if self.separate_broadcast_address:
            response[ble_json]["separateBroadcastAddress"] = \
                self.separate_broadcast_address
        if self.pairing_null:
            response[ble_json][
                "urn:ietf:params:scim:schemas:extension:pairingNull:2.0:Device"] = self.pairing_null
        if self.pairing_just_works_key:
            response[ble_json][
                "urn:ietf:params:scim:schemas:extension:pairingJustWorks:2.0:Device"] = {
                    "key": self.pairing_just_works_key
            }
        if self.pairing_pass_key is not None:
            response[ble_json][
                "urn:ietf:params:scim:schemas:extension:pairingPassKey:2.0:Device"] = {
                    "key": self.pairing_pass_key
            }
        if self.pairing_oob_key:
            response[ble_json][
                "urn:ietf:params:scim:schemas:extension:pairingOOB:2.0:Device"] = {
                    "key": self.pairing_oob_key,
                    "randNumber": self.pairing_oobrn
            }
        return response

class GattTopic(db.Model):
    """ Define topics for GATT services and their data formats. """
    __tablename__ = "gatt_topics"

    topic = Column(String(), primary_key=True, unique=True)
    service_uuid = Column(String())
    characteristic_uuid = Column(String())
    data_format = Column(Enum("default", "payload", name="data_format"))

    devices: Mapped[List[BleExtension]] = relationship(
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
    devices: Mapped[List[BleExtension]] = relationship(
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
        return f"<topic {self.topic}>"


class ConnectionTopic(db.Model):
    """ Define topics for BLE connection status updates. """
    __tablename__ = "connection_topics"

    topic = Column(String(), primary_key=True, unique=True)
    data_format = Column(Enum("default", "payload", name="data_format"))
    devices: Mapped[List[BleExtension]] = relationship(
        secondary=connection_topic_devices, back_populates="connection_topics")

    def __init__(self, topic: str, data_format, devices: Any):
        self.topic = topic
        self.data_format = data_format
        self.devices.extend(devices)


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
