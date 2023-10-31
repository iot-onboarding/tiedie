# Copyright (c) 2023, Cisco and/or its affiliates.
# All rights reserved.
# See LICENSE file in this distribution.
# SPDX-License-Identifier: Apache-2.0

"""

This module integrates Flask, SQLAlchemy, and Paho MQTT for managing
Bluetooth Low Energy device data and MQTT communication in a project.

"""

import dataclasses
from flask import Flask
import paho.mqtt.client as mqtt
from sqlalchemy import Column, func, and_, select
from database import session
from models import AdvTopic, GattTopic, User
from proto import data_app_pb2


@dataclasses.dataclass
class AdvField:
    """
    Represents an advertising field with length, type, and data properties.
    It provides a method from_bytes for creating AdvField objects from bytes.
    """

    length: int
    adtype: str
    data: str

    @staticmethod
    def from_bytes(seq: bytes):
        """ function from_bytes """
        ads: list[AdvField] = []

        while seq:
            length = seq[0]
            if length == 0:
                break
            adtype = seq[1]
            data = seq[2:length + 1]
            ads.append(AdvField(length, adtype.to_bytes(
                1, byteorder='big').hex(), data.hex()))
            seq = seq[length + 1:]

        return ads


def is_filter_match(value: str, topic_filter: Column[str] | str) -> bool:
    """ Checks if a value matches a filter (filter can contain wildcards). """
    if topic_filter == "*":
        return True

    leading_wildcard = topic_filter.startswith("*")
    trailing_wildcard = topic_filter.endswith("*")
    raw_filter = topic_filter.replace("*", "")

    if leading_wildcard and trailing_wildcard:
        return raw_filter in value

    if leading_wildcard:
        return value.endswith(raw_filter)

    if trailing_wildcard:
        return value.startswith(raw_filter)

    return value == raw_filter


def is_adv_allowed(topic: AdvTopic, adv_fields: list[AdvField], address: str) -> bool:
    """ Determines if an advertisement is allowed based on the topic filters. """
    if len(topic.filters) == 0:
        return True

    is_default_allow = bool(topic.filter_type == "deny")

    count = 0

    mac = address.lower().replace(":", "")

    for adv in adv_fields:
        for topic_filter in topic.filters:
            if is_filter_match(mac, topic_filter.mac_filter) and \
                is_filter_match(adv.type, topic_filter.ad_type_filter) and \
                    is_filter_match(adv.data, topic_filter.ad_data_filter):
                if is_default_allow:
                    count += 1
                    break
                return True

    if is_default_allow and len(adv_fields) == count:
        return False

    return is_default_allow


class DataProducer:
    """
    Handles data production and publishing over MQTT.
    It has methods for publishing notifications, advertisements, and
    connection status.
    """
    mqtt_client: mqtt.Client

    def __init__(self, mqtt_client: mqtt.Client, app: Flask):
        self.mqtt_client = mqtt_client
        self.app = app

    def publish_notification(self,
                             mac_address: str,
                             service_uuid: str,
                             char_uuid: str,
                             value: bytes):
        """ Publish GATT notifications/indications to registered MQTT topics """
        with self.app.app_context():
            user = session.scalar(select(User)
                                  .join(GattTopic, User.gatt_topics)
                                  .where(and_(User.device_mac_address == mac_address,
                                              GattTopic.service_uuid == service_uuid,
                                              GattTopic.characteristic_uuid == char_uuid)))

            if user is None:
                return

            for topic in user.gatt_topics:
                ble_sub = data_app_pb2.DataSubscription()  # pylint: disable=no-member
                ble_sub.data = value

                if topic.data_format == "default":
                    ble_sub.device_id = str(user.id)
                    # pylint: disable-next=no-member
                    ble_subscription = data_app_pb2.DataSubscription.BLESubscription()
                    ble_subscription.service_uuid = service_uuid
                    ble_subscription.characteristic_uuid = char_uuid
                    ble_sub.ble_subscription.CopyFrom(ble_subscription)

                self.mqtt_client.publish(
                    topic.topic, ble_sub.SerializeToString())

    def publish_advertisement(self, evt):
        """ Publishes filtered BLE advertisements to MQTT topics based on conditions. """
        with self.app.app_context():
            user = session.scalar(select(User).filter(
                func.lower(User.device_mac_address) == func.lower(evt.address)))

            adv_topics = list(session.scalars(
                select(AdvTopic).filter_by(onboarded=False)).all())

            ble_adv = data_app_pb2.DataSubscription()  # pylint: disable=no-member
            ble_adv.data = evt.data
            # pylint: disable-next=no-member
            ble_advertisement = data_app_pb2.DataSubscription.BLEAdvertisement()
            ble_advertisement.rssi = evt.rssi
            ble_advertisement.mac_address = evt.address
            ble_adv.ble_advertisement.CopyFrom(ble_advertisement)

            adv_fields = AdvField.from_bytes(evt.data)

            if user is not None:
                ble_adv.device_id = str(user.id)
                adv_topics.extend(user.adv_topics)

            for topic in adv_topics:
                if is_adv_allowed(topic, adv_fields, evt.address):
                    self.mqtt_client.publish(
                        str(topic.topic), ble_adv.SerializeToString())

    def publish_connection_status(self, evt, address, connected: bool):
        """ Publishes BLE connection status updates to MQTT topics based on conditions. """
        with self.app.app_context():
            user = session.scalar(select(User).filter(
                func.lower(User.device_mac_address) == func.lower(address)))

            if user is None:
                return

            ble_connection = data_app_pb2.DataSubscription()  # pylint: disable=no-member
            ble_connection.device_id = str(user.id)
            # pylint: disable-next=no-member
            ble_connection_status = data_app_pb2.DataSubscription.BLEConnectionStatus()
            ble_connection_status.mac_address = address
            ble_connection_status.connected = connected
            if not connected:
                ble_connection_status.reason = evt.reason

            ble_connection.ble_connection_status.CopyFrom(
                ble_connection_status)

            for connection_topic in user.connection_topics:
                self.mqtt_client.publish(
                    topic=str(connection_topic.topic),
                    payload=ble_connection.SerializeToString(),
                    qos=1,
                    retain=True
                )
