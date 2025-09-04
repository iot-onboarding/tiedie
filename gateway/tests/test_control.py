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
import base64
import urllib.parse
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
from nipc_models import SdfModel
# pylint: disable-next=unused-import
from scim_fdo import FDOExtension
# pylint: disable-next=unused-import
from scim_ethermab import EtherMABExtension

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

@pytest.fixture(name="data_app")
def fixture_data_app(client: FlaskClient, api_key: str):
    """ Test POST Data App """
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

    assert response.json is not None

    return response.json

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
        f"/nipc/devices/{device['id']}/connections",
        headers={
            "x-api-key": control_api_key
        },
        json={
            "retries": 3,
            "retryMultipleAPs": True
        }
    )

    assert response.status_code == 200
    assert response.json is not None
    assert response.json.get("id") == device["id"]
    if "sdfProtocolMap" in response.json:
        assert isinstance(response.json["sdfProtocolMap"], dict)

    response = client.get(
        f"/nipc/devices/{device['id']}/connections",
        headers={
            "x-api-key": control_api_key
        }
    )

    assert response.status_code == 200
    assert response.json is not None
    assert response.json.get("id") == device["id"]

    # disconnect the device after testing
    response = client.delete(
        f"/nipc/devices/{device['id']}/connections",
        headers={
            "x-api-key": control_api_key
        }
    )

    assert response.status_code == 200
    assert response.json is not None
    assert response.json.get("id") == device["id"]


def test_update_connection(client: FlaskClient, api_key: str, control_api_key: str):
    """ Test updating a device connection service map """
    device = create_device(client, api_key)

    # First connect the device
    response = client.post(
        f"/nipc/devices/{device['id']}/connections",
        headers={
            "x-api-key": control_api_key
        },
        json={
            "retries": 3,
            "retryMultipleAPs": True
        }
    )

    assert response.status_code == 200

    # Test PUT /nipc/devices/{id}/connections - Update service map
    response = client.put(
        f"/nipc/devices/{device['id']}/connections",
        headers={
            "x-api-key": control_api_key
        },
        json={
            "sdfProtocolMap": {
                "ble": {
                    "services": [
                        {
                            "serviceID": "180d",
                            "characteristics": [
                                {
                                    "characteristicID": "2a37",
                                    "descriptors": ["2902"],
                                    "flags": ["notify"]
                                }
                            ]
                        }
                    ]
                }
            }
        }
    )

    assert response.status_code == 200
    assert response.json is not None
    assert response.json.get("id") == device["id"]

    # Test DELETE /nipc/devices/{id}/connections - Disconnect
    response = client.delete(
        f"/nipc/devices/{device['id']}/connections",
        headers={
            "x-api-key": control_api_key
        }
    )

    assert response.status_code == 200
    assert response.json is not None
    assert response.json.get("id") == device["id"]


def test_connection_errors(client: FlaskClient, control_api_key: str):
    """ Test connection error handling with NIPC-compliant Problem Details """
    # Test with non-existent device
    non_existent_device_id = str(uuid.uuid4())

    response = client.post(
        f"/nipc/devices/{non_existent_device_id}/connections",
        headers={
            "x-api-key": control_api_key
        },
        json={
            "retries": 3,
            "retryMultipleAPs": True
        }
    )

    assert response.status_code == 404
    assert response.json is not None
    assert response.json.get("type") == \
        "https://www.iana.org/assignments/nipc-problem-types#invalid-id"
    assert response.json.get("title") == "Not Found"
    assert response.json.get("status") == 404


def test_property_read_with_explicit_connection(client: FlaskClient, api_key: str,
                                               control_api_key: str, sdf_model: SdfModel):  # pylint: disable=unused-argument
    """Test property read with explicit device connection"""
    device = create_device(client, api_key)

    # Explicitly connect the device
    response = client.post(
        f"/nipc/devices/{device['id']}/connections",
        headers={"x-api-key": control_api_key},
        json={"retries": 3, "retryMultipleAPs": True}
    )
    assert response.status_code == 200
    assert response.json.get("id") == device["id"]

    # Perform a property read while connected
    property_name = ("https://example.com/thermometer#/sdfThing/thermometer/"
                     "sdfProperty/temperature")
    encoded_property = urllib.parse.quote(property_name)
    response = client.get(
        f"/nipc/devices/{device['id']}/properties?propertyName={encoded_property}",
        headers={"x-api-key": control_api_key}
    )
    assert response.status_code == 200
    assert response.json is not None
    assert isinstance(response.json, list)
    assert len(response.json) == 1
    result = response.json[0]
    assert result.get("property") == property_name
    assert "value" in result
    assert isinstance(result["value"], str)

    # Optionally, verify connection status is still connected
    response = client.get(
        f"/nipc/devices/{device['id']}/connections",
        headers={"x-api-key": control_api_key}
    )
    assert response.status_code == 200
    assert response.json.get("id") == device["id"]

    # Disconnect the device after testing
    response = client.delete(
        f"/nipc/devices/{device['id']}/connections",
        headers={"x-api-key": control_api_key}
    )
    assert response.status_code == 200
    assert response.json.get("id") == device["id"]


def test_property_read_with_auto_connection(client: FlaskClient, api_key: str,
                                           control_api_key: str, sdf_model: SdfModel):  # pylint: disable=unused-argument
    """ Test property read with automatic connection management """
    device = create_device(client, api_key)

    # Test reading a property when device is not connected
    property_name = ("https://example.com/thermometer#/sdfThing/thermometer/"
                     "sdfProperty/temperature")
    encoded_property = urllib.parse.quote(property_name, safe='')

    response = client.get(
        f"/nipc/devices/{device['id']}/properties?propertyName={encoded_property}",
        headers={
            "x-api-key": control_api_key
        }
    )

    assert response.status_code == 200
    assert response.json is not None
    assert isinstance(response.json, list)
    assert len(response.json) == 1

    result = response.json[0]
    assert result.get("property") == property_name
    assert "value" in result
    # Value should be base64 encoded
    assert isinstance(result["value"], str)

    # Verify the device was automatically disconnected after the operation
    # (we can't directly test this without mocking, but the endpoint should handle it)


def test_property_read_multiple_properties(client: FlaskClient, api_key: str,
                                          control_api_key: str, sdf_model: SdfModel):  # pylint: disable=unused-argument
    """ Test reading multiple properties """
    device = create_device(client, api_key)

    # Test reading multiple properties
    temp_property = ("https://example.com/thermometer#/sdfThing/thermometer/"
                     "sdfProperty/temperature")
    humidity_property = ("https://example.com/thermometer#/sdfThing/thermometer/"
                         "sdfProperty/humidity")

    response = client.get(
        f"/nipc/devices/{device['id']}/properties?"
        f"propertyName={urllib.parse.quote(temp_property, safe='')}&"
        f"propertyName={urllib.parse.quote(humidity_property, safe='')}",
        headers={
            "x-api-key": control_api_key
        }
    )

    assert response.status_code == 200
    assert response.json is not None
    assert isinstance(response.json, list)
    assert len(response.json) == 2

    # Check that both properties are returned
    properties = [result.get("property") for result in response.json]
    assert temp_property in properties
    assert humidity_property in properties


def test_property_write_with_auto_connection(client: FlaskClient, api_key: str,
                                            control_api_key: str, sdf_model: SdfModel):  # pylint: disable=unused-argument
    """ Test property write with automatic connection management """
    device = create_device(client, api_key)

    # Test writing a property when device is not connected
    property_name = ("https://example.com/thermometer#/sdfThing/thermometer/"
                     "sdfProperty/temperature_control")
    test_value = base64.b64encode(b"25.5").decode('ascii')

    response = client.put(
        f"/nipc/devices/{device['id']}/properties",
        json=[{
            "property": property_name,
            "value": test_value
        }],
        headers={
            "x-api-key": control_api_key
        }
    )

    assert response.status_code == 200
    assert response.json is not None
    assert isinstance(response.json, list)
    assert len(response.json) == 1

    result = response.json[0]
    assert result.get("status") == 200


def test_property_write_readonly_property(client: FlaskClient, api_key: str,
                                         control_api_key: str, sdf_model: SdfModel):  # pylint: disable=unused-argument
    """ Test writing to a read-only property """
    device = create_device(client, api_key)

    # Test writing to a read-only property (temperature - read only)
    property_name = ("https://example.com/thermometer#/sdfThing/thermometer/"
                     "sdfProperty/temperature")
    test_value = base64.b64encode(b"25.5").decode('ascii')

    response = client.put(
        f"/nipc/devices/{device['id']}/properties",
        json=[{
            "property": property_name,
            "value": test_value
        }],
        headers={
            "x-api-key": control_api_key
        }
    )

    assert response.status_code == 200
    assert response.json is not None
    assert isinstance(response.json, list)
    assert len(response.json) == 1

    result = response.json[0]
    assert result.get("type") == ("https://www.iana.org/assignments/"
                                  "nipc-problem-types#property-not-writable")
    assert result.get("status") == 400
    assert "not writable" in result.get("detail", "").lower()


def test_property_invalid_sdf_reference(client: FlaskClient, api_key: str,
                                       control_api_key: str, sdf_model: SdfModel):  # pylint: disable=unused-argument
    """ Test property operations with invalid SDF reference """
    device = create_device(client, api_key)

    # Test with invalid SDF reference
    invalid_property = ("https://example.com/nonexistent#/sdfThing/invalid/"
                        "sdfProperty/test")

    response = client.get(
        f"/nipc/devices/{device['id']}/properties?"
        f"propertyName={urllib.parse.quote(invalid_property, safe='')}",
        headers={
            "x-api-key": control_api_key
        }
    )

    assert response.status_code == 200
    assert response.json is not None
    assert isinstance(response.json, list)
    assert len(response.json) == 1

    result = response.json[0]
    assert result.get("type") == ("https://www.iana.org/assignments/"
                                  "nipc-problem-types#invalid-sdf-url")
    assert result.get("status") == 400


def test_property_nonexistent_device(client: FlaskClient, control_api_key: str):
    """ Test property operations on non-existent device """
    non_existent_device_id = str(uuid.uuid4())
    property_name = ("https://example.com/thermometer#/sdfThing/thermometer/"
                     "sdfProperty/temperature")

    # Test read
    response = client.get(
        f"/nipc/devices/{non_existent_device_id}/properties?"
        f"propertyName={urllib.parse.quote(property_name, safe='')}",
        headers={
            "x-api-key": control_api_key
        }
    )

    assert response.status_code == 404
    assert response.json is not None
    assert response.json.get("type") == ("https://www.iana.org/assignments/"
                                         "nipc-problem-types#invalid-id")
    assert response.json.get("status") == 404

    # Test write
    response = client.put(
        f"/nipc/devices/{non_existent_device_id}/properties",
        json=[{
            "property": property_name,
            "value": base64.b64encode(b"25.5").decode('ascii')
        }],
        headers={
            "x-api-key": control_api_key
        }
    )

    assert response.status_code == 404
    assert response.json is not None
    assert response.json.get("type") == ("https://www.iana.org/assignments/"
                                         "nipc-problem-types#invalid-id")
    assert response.json.get("status") == 404


def test_property_missing_parameters(client: FlaskClient, api_key: str,
                                    control_api_key: str):
    """ Test property operations with missing parameters """
    device = create_device(client, api_key)

    # Test read without propertyName parameter
    response = client.get(
        f"/nipc/devices/{device['id']}/properties",
        headers={
            "x-api-key": control_api_key
        }
    )

    assert response.status_code == 400
    assert response.json is not None
    assert response.json.get("type") == ("https://www.iana.org/assignments/"
                                         "nipc-problem-types#invalid-sdf-url")
    assert response.json.get("status") == 400

    # Test write without request body
    response = client.put(
        f"/nipc/devices/{device['id']}/properties",
        headers={
            "x-api-key": control_api_key
        }
    )

    assert response.status_code == 400
    assert response.json is not None
    assert response.json.get("type") == ("https://www.iana.org/assignments/"
                                         "nipc-problem-types#invalid-sdf-url")


def test_register_data_app(
    client: FlaskClient,
    control_api_key: str,
    sdf_model: SdfModel, # pylint: disable=unused-argument
    data_app: dict) -> None:
    """ Test complete data app CRUD operations """
    data_app_id = data_app["id"]
    initial_request_body = {
        "events": [
            {
                "event": "https://example.com/thermometer"
                         "#/sdfThing/thermometer/sdfEvent/isPresent"
            }
        ],
        "mqttClient": True
    }

    # Test 1: Register data app (POST)
    response = client.post(
        f"/nipc/registrations/data-apps?dataAppId={data_app_id}",
        json=initial_request_body,
        headers={
            "x-api-key": control_api_key
        }
    )

    assert response.status_code == 200
    assert response.json == initial_request_body

    # Test 2: Get data app (GET)
    response = client.get(
        f"/nipc/registrations/data-apps?dataAppId={data_app_id}",
        headers={
            "x-api-key": control_api_key
        }
    )

    assert response.status_code == 200
    assert response.json == initial_request_body

    # Test 3: Update data app (PUT)
    updated_request_body = {
        "events": [
            {
                "event": "https://example.com/thermometer"
                         "#/sdfThing/thermometer/sdfEvent/isConnected"
            }
        ],
        "mqttClient": True
    }

    response = client.put(
        f"/nipc/registrations/data-apps?dataAppId={data_app_id}",
        json=updated_request_body,
        headers={
            "x-api-key": control_api_key
        }
    )

    print(response.json)

    assert response.status_code == 200
    assert response.json == updated_request_body

    # Test 4: Verify update by getting data app again
    response = client.get(
        f"/nipc/registrations/data-apps?dataAppId={data_app_id}",
        headers={
            "x-api-key": control_api_key
        }
    )

    assert response.status_code == 200
    assert response.json == updated_request_body

    # Test 5: Delete data app (DELETE)
    response = client.delete(
        f"/nipc/registrations/data-apps?dataAppId={data_app_id}",
        headers={
            "x-api-key": control_api_key
        }
    )

    assert response.status_code == 200
    assert response.json == updated_request_body  # Should return what was deleted

    # Test 6: Verify deletion by trying to get non-existent data app
    response = client.get(
        f"/nipc/registrations/data-apps?dataAppId={data_app_id}",
        headers={
            "x-api-key": control_api_key
        }
    )

    assert response.status_code == 404
    assert response.json is not None
    assert response.json.get("type") == "about:blank"
    assert response.json.get("status") == 404
    assert f"Data app with ID {data_app_id} not found" in response.json.get("detail", "")


def test_device_events(
    client: FlaskClient,
    api_key: str,
    control_api_key: str,
    sdf_model: SdfModel) -> None:  # pylint: disable=unused-argument
    """ Test complete device event CRUD operations """
    # First create a device to test events on
    device = create_device(client, api_key)
    device_id = device['id']

    # Test 1: Enable event (POST)
    event_name = "https://example.com/thermometer#/sdfThing/thermometer/sdfEvent/isPresent"
    encoded_event_name = urllib.parse.quote(event_name)
    response = client.post(
        f"/nipc/devices/{device_id}/events?eventName={encoded_event_name}",
        headers={
            "x-api-key": control_api_key
        }
    )

    assert response.status_code == 201
    assert "Location" in response.headers
    # Extract instance ID from Location header
    location_header = response.headers["Location"]
    print(location_header)
    instance_id = location_header.split("instanceId=")[1]

    # Test 2: Get event (GET)
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

    # Test 3: Enable second event (POST)
    event_name2 = "https://example.com/thermometer#/sdfThing/thermometer/sdfEvent/isConnected"
    encoded_event_name2 = urllib.parse.quote(event_name2)
    response = client.post(
        f"/nipc/devices/{device_id}/events?eventName={encoded_event_name2}",
        headers={
            "x-api-key": control_api_key
        }
    )

    assert response.status_code == 201
    location_header2 = response.headers["Location"]
    instance_id2 = location_header2.split("instanceId=")[1]

    # Test 4: Get multiple events (GET)
    response = client.get(
        f"/nipc/devices/{device_id}/events?instanceId={instance_id}&instanceId={instance_id2}",
        headers={
            "x-api-key": control_api_key
        }
    )

    assert response.status_code == 200
    assert response.json is not None
    assert len(response.json) == 2
    events = {event["event"]: event["instanceId"] for event in response.json}
    assert event_name in events
    assert event_name2 in events
    assert events[event_name] == instance_id
    assert events[event_name2] == instance_id2

    # Test 5: Disable first event (DELETE)
    response = client.delete(
        f"/nipc/devices/{device_id}/events?instanceId={instance_id}",
        headers={
            "x-api-key": control_api_key
        }
    )

    assert response.status_code == 204

    # Test 6: Verify first event is deleted
    response = client.get(
        f"/nipc/devices/{device_id}/events?instanceId={instance_id}",
        headers={
            "x-api-key": control_api_key
        }
    )

    assert response.status_code == 400
    assert "Event for device ID" in response.json.get("detail", "")

    # Test 7: Verify second event still exists
    response = client.get(
        f"/nipc/devices/{device_id}/events?instanceId={instance_id2}",
        headers={
            "x-api-key": control_api_key
        }
    )

    assert response.status_code == 200
    assert len(response.json) == 1
    assert response.json[0]["event"] == event_name2

    # Test 8: Disable second event (DELETE)
    response = client.delete(
        f"/nipc/devices/{device_id}/events?instanceId={instance_id2}",
        headers={
            "x-api-key": control_api_key
        }
    )

    assert response.status_code == 204


def test_duplicate_event_enable(
    client: FlaskClient,
    api_key: str,
    control_api_key: str,
    sdf_model: SdfModel) -> None:  # pylint: disable=unused-argument
    """ Test enabling duplicate events """
    device = create_device(client, api_key)
    device_id = device['id']

    event_name = "https://example.com/thermometer#/sdfThing/thermometer/sdfEvent/isPresent"
    encoded_event_name = urllib.parse.quote(event_name)

    # Enable event first time
    response = client.post(
        f"/nipc/devices/{device_id}/events?eventName={encoded_event_name}",
        headers={
            "x-api-key": control_api_key
        }
    )

    assert response.status_code == 201

    # Try to enable same event again
    response = client.post(
        f"/nipc/devices/{device_id}/events?eventName={encoded_event_name}",
        headers={
            "x-api-key": control_api_key
        }
    )

    assert response.status_code == 400
    assert "Event already exists" in response.json.get("detail", "")
