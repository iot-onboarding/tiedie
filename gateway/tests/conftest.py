"""
Pytest bootstrap for gateway tests.

Centralize shared fixtures and enable optional SCIM extensions via create_app
options, without relying on environment-variable import ordering.
"""

import os
import uuid

import paho.mqtt.client as mqtt
import pytest
from flask import Flask
from flask.testing import FlaskClient
from paho.mqtt.enums import CallbackAPIVersion
from testcontainers.postgres import PostgresContainer

from app_factory import create_app
from data_producer import DataProducer
from database import db
from models import OnboardingAppKey
from nipc_models import SdfModel
from tests.mosquitto_container import MosquittoContainer


@pytest.fixture(name="postgres")
def fixture_postgres():
    """Postgres container."""
    with PostgresContainer("postgres:13.1") as postgres_container:
        yield postgres_container


@pytest.fixture(name="app")
def fixture_app(postgres: PostgresContainer):
    """Flask application."""
    app = create_app(
        postgres.get_connection_url(),
        want_ether_mab=True,
        want_fdo=True,
    )

    with app.app_context():
        db.create_all()

    yield app


@pytest.fixture(name="client")
def fixture_client(app: Flask) -> FlaskClient:
    """Flask client."""
    return app.test_client()


@pytest.fixture(name="api_key")
def fixture_api_key(app):
    """Create onboarding API key for testing."""
    with app.app_context():
        key = uuid.uuid4()
        authkey = OnboardingAppKey("onboarding-app", str(key))
        db.session.add(authkey)
        db.session.commit()
        yield key


@pytest.fixture(name="mosquitto")
def fixture_mosquitto():
    """Mosquitto container."""
    path = os.path.abspath(os.path.dirname(__file__))
    with MosquittoContainer(volume_mappings=[
        (path + "/mosquitto.conf", "/mosquitto/config/mosquitto.conf"),
    ]) as m_container:
        yield m_container


@pytest.fixture(name="mqtt_client")
def fixture_mqtt_client(mosquitto: MosquittoContainer):
    """MQTT client."""
    client = mqtt.Client(CallbackAPIVersion.VERSION2)
    client.connect(mosquitto.get_container_host_ip(),
                   int(mosquitto.get_exposed_port(1883)), 60)
    client.loop_start()
    yield client
    client.disconnect()
    client.loop_stop()


@pytest.fixture(name="data_producer")
def fixture_data_producer(mqtt_client: mqtt.Client, app: Flask):
    """Data producer."""
    yield DataProducer(mqtt_client, app)


@pytest.fixture(name="control_api_key")
def fixture_control_api_key(client: FlaskClient, api_key: str):
    """Create control app and return API key."""
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

    assert response.status_code == 201
    assert response.json is not None

    return response.json.get("clientToken")


@pytest.fixture(name="data_app")
def fixture_data_app(client: FlaskClient, api_key: str):
    """Create telemetry data app."""
    response = client.post(
        "/scim/v2/EndpointApps",
        json={
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:EndpointApp"],
            "applicationType": "telemetry",
            "applicationName": "Telemetry App 1",
        },
        headers={
            "x-api-key": api_key
        }
    )

    assert response.status_code == 201
    assert response.json is not None

    return response.json


@pytest.fixture(name="sdf_model")
def fixture_sdf_model(app: Flask):
    """Create test SDF model."""
    with app.app_context():
        model = {
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
                            "sdfProtocolMap": {
                                "ble": {
                                    "type": "advertisements"
                                }
                            }
                        },
                        "isConnected": {
                            "description": "BLE connection event",
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
        sdf_model = SdfModel(sdf_name="https://example.com/thermometer",
                             model=model)
        db.session.add(sdf_model)
        db.session.commit()
        yield sdf_model
