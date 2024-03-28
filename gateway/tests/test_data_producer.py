# Copyright (c) 2023, Cisco Systems, Inc. and/or its affiliates.
# All rights reserved.
# See LICENSE file in this distribution.
# SPDX-License-Identifier: Apache-2.0

"""
Test gateway data producer.
"""

import os
import time
import uuid

import paho.mqtt.client as mqtt
import pytest
from flask import Flask
from flask.testing import FlaskClient
from testcontainers.postgres import PostgresContainer

from app_factory import create_app
from data_producer import DataProducer
from database import db
# pylint: disable-next=unused-import
from models import OnboardingAppKey, Device
# pylint: disable-next=unused-import
from ble_models import BleExtension, GattTopic
from proto import data_app_pb2
from tests.mosquitto_container import MosquittoContainer


@pytest.fixture(name="postgres")
def fixture_postgres():
    """ Postgres container """
    with PostgresContainer("postgres:13.1") as p:
        yield p


@pytest.fixture(name="mosquitto")
def fixture_mosquitto():
    """ Mosquitto container """
    path = os.path.abspath(os.path.dirname(__file__))
    with MosquittoContainer(volume_mappings=[
        (path + "/mosquitto.conf", "/mosquitto/config/mosquitto.conf"),
    ]) as m:
        yield m


@pytest.fixture(name="mqtt_client")
def fixture_mqtt_client(mosquitto: MosquittoContainer):
    """ MQTT client """
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.connect(mosquitto.get_container_host_ip(),
                   int(mosquitto.get_exposed_port(1883)), 60)
    client.loop_start()
    yield client
    client.disconnect()
    client.loop_stop()


@pytest.fixture(name="mqtt_client2")
def fixture_mqtt_client2(mosquitto: MosquittoContainer):
    """ MQTT client """
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.username_pw_set("control-app", "test")
    client.connect(mosquitto.get_container_host_ip(),
                   int(mosquitto.get_exposed_port(1883)), 60)
    client.loop_start()
    yield client
    client.disconnect()
    client.loop_stop()


@pytest.fixture(name="app")
def fixture_app(postgres: PostgresContainer):
    """ Flask application """
    app = create_app(postgres.get_connection_url())

    with app.app_context():
        db.create_all()

    yield app


@pytest.fixture(name="client")
def fixture_client(app: Flask) -> FlaskClient:
    """ Flask client """
    return app.test_client()


@pytest.fixture(name="api_key")
def fixture_api_key(app):
    """ Create onboarding API key for testing """
    with app.app_context():
        key = uuid.uuid4()
        authkey = OnboardingAppKey("onboarding-app", str(key))
        db.session.add(authkey)
        db.session.commit()
        yield key


@pytest.fixture(name="data_producer")
def fixture_data_producer(mqtt_client: mqtt.Client, app: Flask):
    """ Data producer """
    yield DataProducer(mqtt_client, app)


def test_publish_notification(mqtt_client2: mqtt.Client,
                              data_producer: DataProducer,
                              client: FlaskClient,
                              api_key: str):
    """ Test publish notification """

    response = client.post(
        "/scim/v2/EndpointApps",
        json={
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:EndpointApp"],
            "applicationType": "deviceControl",
            "applicationName": "control-app",
        },
        headers={
            "x-api-key": api_key
        }
    )

    assert response.status_code == 201

    control_app_id = response.json["id"]
    control_api_key = response.json["clientToken"]

    response = client.post(
        "/scim/v2/Devices",
        json={
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Device",
                        "urn:ietf:params:scim:schemas:extension:ble:2.0:Device"],
            "deviceDisplayName": "BLE Heart Monitor",
            "adminState": True,
            "urn:ietf:params:scim:schemas:extension:ble:2.0:Device": {
                "versionSupport": ["5.3"],
                "deviceMacAddress": "AA:BB:CC:11:22:33",
                "isRandom": False,
                "mobility": True
            },
            "urn:ietf:params:scim:schemas:extension:endpointAppExt:2.0:Device": {
                "applications": [
                    {
                        "value": control_app_id
                    }
                ]
            }
        }, headers={
            "x-api-key": api_key
        }
    )

    assert response.status_code == 201
    device_id = response.json["id"]

    response = client.post(
        "/nipc/registration/topic",
        json={
            "id": device_id,
            "topic": "ble/notifications",
            "dataFormat": "default",
            "ble": {
                "type": "gatt",
                "serviceID": "180d",
                "characteristicID": "2a37"
            }
        }, headers={
            "x-api-key": control_api_key
        }
    )

    assert response.status_code == 200

    def on_message(_client, _userdata, message: mqtt.MQTTMessage):
        print(
            f"Received message '{message.payload}' on topic '{message.topic}'")
        data_subscription = data_app_pb2.DataSubscription()  # pylint: disable=no-member
        data_subscription.ParseFromString(message.payload)
        assert data_subscription.device_id == device_id
        assert data_subscription.ble_subscription.service_uuid == "180d"
        assert data_subscription.ble_subscription.characteristic_uuid == "2a37"
        assert data_subscription.data == b"\x00\x00"

    mqtt_client2.on_message = on_message
    mqtt_client2.subscribe("ble/notifications")

    data_producer.publish_notification("AA:BB:CC:11:22:33",
                                       "180d",
                                       "2a37",
                                       b"\x00\x00")

    # wait for on_message callback to be fired
    time.sleep(1)
