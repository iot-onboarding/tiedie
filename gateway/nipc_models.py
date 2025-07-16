# Copyright (c) 2024, Cisco Systems, Inc. and/or its affiliates.
# All rights reserved.
# See LICENSE file in this distribution.
# SPDX-License-Identifier: Apache-2.0

"""

This script defines SQLAlchemy models for BLE database interactions,
representing GATT topics, and filters for a web application.

"""

from typing import Optional
import uuid

from sqlalchemy import (
    JSON,
    Boolean,
    ForeignKey,
    Integer,
    String,
    ARRAY,
    BigInteger
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, relationship, mapped_column
from database import db
from models import Device

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


class SdfModel(db.Model):
    """Represents a registered SDF model for a class of devices."""
    __tablename__ = "sdf_model"

    id = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sdf_name = mapped_column(String, unique=True, nullable=False, index=True)
    model = mapped_column(JSON, nullable=False)

    def __init__(self, sdf_name: str, model: dict):
        self.sdf_name = sdf_name
        self.model = model

    def serialize(self) -> dict:
        """Serialize the SDF model to a dictionary."""
        return {
                "sdfName": self.sdf_name
            }

class DataApp(db.Model):
    """Represents a registered data application."""
    __tablename__ = "data_app"

    data_app_id = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("endpoint_app.id"),
        primary_key=True,
        default=uuid.uuid4
    )
    # events is an array of strings
    events = mapped_column(ARRAY(String))

    def __init__(self, data_app_id: str, events: list[str]):
        self.data_app_id = data_app_id
        self.events = events

class Event(db.Model):
    """Represents an event."""
    __tablename__ = "event"

    instance_id = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_name = mapped_column(String, unique=True, nullable=False)
    device_id = mapped_column(UUID(as_uuid=True), ForeignKey("devices.device_id"), nullable=False)
    # event type can be "advertisements", "connection_events", "gatt"
    event_type = mapped_column(String, nullable=False)
    gatt_service_id = mapped_column(String, nullable=True)
    gatt_characteristic_id = mapped_column(String, nullable=True)

    def __init__(
            self,
            event_name: str,
            instance_id: UUID,
            device_id: str,
            event_type: str,
            gatt_service_id: Optional[str],
            gatt_characteristic_id: Optional[str]
    ):
        self.event_name = event_name
        self.instance_id = instance_id
        self.device_id = device_id
        self.event_type = event_type
        self.gatt_service_id = gatt_service_id
        self.gatt_characteristic_id = gatt_characteristic_id
