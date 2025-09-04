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
import urllib.parse
import cbor2
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
from nipc_models import BleExtension, SdfModel
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


@pytest.fixture(name="sdf_model")
def fixture_sdf_model(app: Flask):
    """ Create test SDF model """
    with app.app_context():
        sdf_model = SdfModel(
            sdf_name="https://example.com/thermometer",
            model={
                "namespace": {"tm": "https://example.com/thermometer"},
                "sdfThing": {
                    "thermometer": {
                        "sdfProperty": {
                            "temperature": {
                                "type": "number",
                                "minimum": -40,
                                "maximum": 125,
                                "unit": "Cel",
                                "writable": False,
                                "sdfProtocolMap": {
                                    "ble": {
                                        "serviceID": "180d",
                                        "characteristicID": "2a38"
                                    }
                                }
                            },
                            "temperature_control": {
                                "type": "number",
                                "minimum": -40,
                                "maximum": 125,
                                "unit": "Cel",
                                "writable": True,
                                "sdfProtocolMap": {
                                    "ble": {
                                        "serviceID": "180d",
                                        "characteristicID": "2a39"
                                    }
                                }
                            },
                            "humidity": {
                                "type": "number",
                                "minimum": 0,
                                "maximum": 100,
                                "unit": "%",
                                "writable": False,
                                "sdfProtocolMap": {
                                    "ble": {
                                        "serviceID": "180d",
                                        "characteristicID": "2a38"
                                    }
                                }
                            }
                        },
                        "sdfEvent": {
                            "isPresent": {
                                "description": "BLE advertisements",
                                "sdfOutputData": {
                                    "sdfProtocolMap": {
                                        "ble": {
                                            "type": "advertisements"
                                        }
                                    }
                                }
                            },
                            "isConnected": {
                                "description": "BLE connection event",
                                "sdfOutputData": {
                                    "sdfProtocolMap": {
                                        "ble": {
                                            "type": "connection_events"
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        )
        db.session.add(sdf_model)
        db.session.commit()
        yield sdf_model


@pytest.fixture(name="control_api_key")
def fixture_control_api_key(client: FlaskClient, api_key: str):
    """ Create control app and return API key """
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
    assert response.json is not None

    return response.json.get("clientToken")


@pytest.fixture(name="data_app")
def fixture_data_app(client: FlaskClient, api_key: str):
    """ Create telemetry data app """
    response = client.post(
        "/scim/v2/EndpointApps",
        json={
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:EndpointApp"],
            "applicationType": "telemetry",
            "applicationName": "Telemetry Data App",
        },
        headers={
            "x-api-key": api_key
        }
    )

    assert response.status_code == 201
    assert response.json is not None

    return response.json


@pytest.fixture(name="device")
def fixture_device(client: FlaskClient, api_key: str):
    """ Create BLE device """
    response = client.post(
        "/scim/v2/Devices",
        json={
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Device",
                        "urn:ietf:params:scim:schemas:extension:ble:2.0:Device"],
            "displayName": "BLE Heart Monitor",
            "active": True,
            "urn:ietf:params:scim:schemas:extension:ble:2.0:Device": {
                "versionSupport": ["5.3"],
                "deviceMacAddress": "AA:BB:CC:11:22:33",
                "isRandom": False,
                "mobility": True
            }
        }, headers={
            "x-api-key": api_key
        }
    )

    assert response.status_code == 201
    assert response.json is not None

    return response.json


@pytest.fixture(name="registered_data_app")
def fixture_registered_data_app(client: FlaskClient, data_app: dict, sdf_model: SdfModel):  # pylint: disable=unused-argument
    """ Register data app with events """
    data_app_id = data_app["id"]
    data_app_token = data_app["clientToken"]
    event_name = "https://example.com/thermometer#/sdfThing/thermometer/sdfEvent/isPresent"

    data_app_registration = {
        "events": [
            {
                "event": event_name
            }
        ],
        "mqttClient": True
    }

    response = client.post(
        f"/nipc/registrations/data-apps?dataAppId={data_app_id}",
        json=data_app_registration,
        headers={
            "x-api-key": data_app_token
        }
    )

    assert response.status_code == 200
    assert response.json == data_app_registration

    return {
        "data_app_id": data_app_id,
        "event_name": event_name,
        "registration": data_app_registration
    }


def test_publish_notification(mqtt_client2: mqtt.Client,
                              data_producer: DataProducer,
                              client: FlaskClient,
                              control_api_key: str,
                              device: dict,
                              registered_data_app: dict,
                              sdf_model: SdfModel):  # pylint: disable=unused-argument
    """ Test publish notification with data app registration and event subscription """
    # Get values from fixtures
    device_id = device["id"]
    data_app_id = registered_data_app["data_app_id"]
    event_name = registered_data_app["event_name"]

    # Step 1: Enable event on the device (similar to test_device_events)
    encoded_event_name = urllib.parse.quote(event_name)
    response = client.post(
        f"/nipc/devices/{device_id}/events?eventName={encoded_event_name}",
        headers={
            "x-api-key": control_api_key
        }
    )

    assert response.status_code == 201
    assert "Location" in response.headers
    location_header = response.headers["Location"]
    instance_id = location_header.split("instanceId=")[1]

    # Step 2: Verify event is enabled
    response = client.get(
        f"/nipc/devices/{device_id}/events?instanceId={instance_id}",
        headers={
            "x-api-key": control_api_key
        }
    )

    assert response.status_code == 200
    assert response.json is not None
    assert len(response.json) == 1
    assert response.json[0]["event"] == event_name
    assert response.json[0]["instanceId"] == instance_id

    # Step 3: Generate topic based on data_producer.py logic and set up MQTT subscription
    # Create topic from event name using the same logic as data_producer.py
    namespace, json_pointer = event_name.split('#', 1)
    expected_topic = f"data-app/{data_app_id}/{namespace}/{json_pointer}"

    def on_message(_client, _userdata, message: mqtt.MQTTMessage):
        print(
            f"Received message '{message.payload}' on topic '{message.topic}'")
        # Verify we received the message on the expected topic
        assert message.topic == expected_topic
        data_subscription = cbor2.loads(message.payload)
        assert data_subscription["deviceID"] == device_id
        assert data_subscription["bleSubscription"]["serviceID"] == "180d"
        assert data_subscription["bleSubscription"]["characteristicID"] == "2a37"
        assert data_subscription["data"] == b"\x00\x00"

    mqtt_client2.on_message = on_message
    mqtt_client2.subscribe(expected_topic)
    print(f"Subscribed to topic: {expected_topic}")

    # Step 4: Publish notification and test end-to-end flow
    data_producer.publish_notification("AA:BB:CC:11:22:33",
                                       "180d",
                                       "2a37",
                                       b"\x00\x00")

    # wait for on_message callback to be fired
    time.sleep(1)
