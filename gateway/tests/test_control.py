# Copyright (c) 2023, Cisco Systems, Inc. and/or its affiliates.
# All rights reserved.
# See LICENSE file in this distribution.
# SPDX-License-Identifier: Apache-2.0
# pylint: disable=consider-using-with

"""
Test Gateway controller implementation
"""

import uuid
import os
from flask import Flask
from flask.testing import FlaskClient
import pytest
from testcontainers.postgres import PostgresContainer
import paho.mqtt.client as mqtt
from paho.mqtt.enums import CallbackAPIVersion
import ap_factory
from app_factory import create_app
from data_producer import DataProducer
from mock.mock_access_point import MockAccessPoint
from models import OnboardingAppKey
from database import db

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


@pytest.fixture(name="mqtt_client")
def fixture_mqtt_client(mosquitto: MosquittoContainer):
    """ MQTT client """
    client = mqtt.Client(CallbackAPIVersion.VERSION2)
    client.connect(mosquitto.get_container_host_ip(),
                   int(mosquitto.get_exposed_port(1883)), 60)
    client.loop_start()
    yield client
    client.disconnect()
    client.loop_stop()


@pytest.fixture(name="ble_ap", autouse=True)
def fixture_ble_ap(data_producer: DataProducer):
    """ BLE Access Point """
    ble_ap = MockAccessPoint(data_producer)
    ap_factory.set_ble_ap(ble_ap)
    ble_ap.start()

    yield ble_ap


@pytest.fixture(name="control_api_key")
def fixture_endpoint_app_token(client: FlaskClient, api_key: str):
    """ Test POST Endpoint Apps """
    response = client.post(
        "/scim/v2/EndpointApps",
        json={
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:EndpointApp"],
            "applicationType": "deviceControl",
            "applicationName": "Device Control App 1",
        },
        headers={
            "x-api-key": api_key
        }
    )

    assert response.json is not None

    return response.json.get("clientToken")


@pytest.fixture(name="data_producer")
def fixture_data_producer(mqtt_client: mqtt.Client, app: Flask):
    """ Data producer """
    yield DataProducer(mqtt_client, app)


def create_device(client: FlaskClient, api_key: str):
    """ Test POST Device """
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

    assert response.json is not None

    return response.json


def test_connect_device(client: FlaskClient, api_key: str, control_api_key: str):
    """ Test connecting a device """
    device = create_device(client, api_key)

    response = client.post(
        "/nipc/connectivity/connection",
        headers={
            "x-api-key": control_api_key
        },
        json={
            "id": device["id"],
            "technology": "ble",
            "ble": {},
            "retries": 3,
            "retryMultipleAPs": True
        }
    )

    assert response.json is not None

    assert response.json == {
        "status": "SUCCESS",
        "requestID": response.json["requestID"],
        "services": [
            {
                "serviceID": "180d",
                "characteristics": [
                    {
                        "characteristicID": "2a37",
                        "descriptors": [
                            {
                                "descriptorID": "2902"
                            }
                        ],
                        "flags": [
                            "notify"
                        ]
                    },
                    {
                        "characteristicID": "2a38",
                        "flags": [
                            "read"
                        ]
                    },
                    {
                        "characteristicID": "2a39",
                        "flags": [
                            "write"
                        ]
                    }
                ]
            }
        ],
    }

    device_id_2 = str(uuid.uuid4())

    response = client.get(
        "/nipc/connectivity/connection",
        headers={
            "x-api-key": control_api_key
        },
        query_string={
            "id": device["id"] + "," + device_id_2
        }
    )

    assert response.json is not None
    assert response.json == {
        "status": "SUCCESS",
        "requestID": response.json["requestID"],
        "connections": [
            {
                "id": device["id"],
                "status": "SUCCESS",
            },
            {
                "id": device_id_2,
                "status": "FAILURE",
            }
        ]
    }

    response = client.get(
        f"/nipc/connectivity/connection/id/{device['id']}",
        headers={
            "x-api-key": control_api_key
        }
    )

    assert response.json is not None
    assert response.json == {
        "status": "SUCCESS",
        "requestID": response.json["requestID"],
        "id": device["id"]
    }
