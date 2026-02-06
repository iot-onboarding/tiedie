# Copyright (c) 2023, Cisco Systems, Inc. and/or its affiliates.
# All rights reserved.
# See LICENSE file in this distribution.
# SPDX-License-Identifier: Apache-2.0

"""

This module integrates Flask, SQLAlchemy, and Paho MQTT for managing
Bluetooth Low Energy device data and MQTT communication in a project.

"""

import time
from typing import Any
import cbor2
from flask import Flask
import paho.mqtt.client as mqtt
from sqlalchemy import func, select
from database import session
from nipc_models import BleExtension, DataApp, Event

def create_topic_from_event(data_app_id: str, event_name: str) -> str:
    """
    Create a topic from an event name.
    
    Args:
        data_app_id: The ID of the data application
        event_name: The name of the event
    
    Returns:
        str: The topic string
    """
    namespace, json_pointer = event_name.split('#', 1)
    return f"data-app/{data_app_id}/{namespace}/{json_pointer}"

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
            device = session.scalar(select(BleExtension).filter(
                func.lower(BleExtension.device_mac_address) == func.lower(mac_address)))

            if device is None:
                return

            gatt_events = list(session.scalars(
                select(Event).filter_by(
                    device_id=device.device_id,
                    event_type="gatt",
                    gatt_service_id=service_uuid,
                    gatt_characteristic_id=char_uuid
                )
            ).all())

            ble_sub: dict[str, Any] = {
                "data": value,
                "timestamp": time.time(),
                "deviceID": str(device.device_id),
                "bleSubscription": {
                    "serviceID": service_uuid,
                    "characteristicID": char_uuid
                }
            }

            for event in gatt_events:
                data_apps = session.scalars(
                    select(DataApp).filter_by(DataApp.events.contains(event.event_name))
                ).all()
                for data_app in data_apps:
                    topic = create_topic_from_event(data_app.data_app_id, event.event_name)

                    data = cbor2.dumps(obj=ble_sub)

                    self.mqtt_client.publish(topic, data)

    def publish_advertisement(self, evt):
        """ Publishes filtered BLE advertisements to MQTT topics based on conditions. """
        with self.app.app_context():
            device = session.scalar(select(BleExtension).filter(
                func.lower(BleExtension.device_mac_address) == func.lower(evt.address)))

            if device is None:
                return

            adv_events = list(session.scalars(
                select(Event).filter_by(
                    device_id=device.device_id,
                    event_type="advertisements")).all())

            ble_adv = {
                "data": evt.data,
                "bleAdvertisement": {
                    "rssi": evt.rssi,
                    "macAddress": evt.address,
                }
            }

            ble_adv["deviceID"] = str(device.device_id)

            data = cbor2.dumps(obj=ble_adv)

            for event in adv_events:
                data_apps = session.scalars(
                    select(DataApp).filter_by(DataApp.events.contains(event.event_name))
                ).all()
                for data_app in data_apps:
                    topic = create_topic_from_event(data_app.data_app_id, event.event_name)
                    self.mqtt_client.publish(topic, data)

    def publish_connection_status(self, evt, address, connected: bool):
        """ Publishes BLE connection status updates to MQTT topics based on conditions. """
        with self.app.app_context():
            device = session.scalar(select(BleExtension).filter(
                func.lower(BleExtension.device_mac_address) == func.lower(address)))

            if device is None:
                return


            ble_connection = {
                "deviceID": str(device.device_id),
                "bleConnectionStatus": {
                    "macAddress": address,
                    "connected": connected,
                    "reason": getattr(evt, "reason", None),
                }
            }

            data = cbor2.dumps(obj=ble_connection)

            connection_events = list(session.scalars(
                select(Event).filter_by(
                    device_id=device.device_id,
                    event_type="connection_events"
                )
            ).all())

            for event in connection_events:
                data_apps = session.scalars(
                    select(DataApp).filter_by(DataApp.events.contains(event.event_name))
                ).all()
                for data_app in data_apps:
                    topic = create_topic_from_event(data_app.data_app_id, event.event_name)
                    self.mqtt_client.publish(topic, data)
