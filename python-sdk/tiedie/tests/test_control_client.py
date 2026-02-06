# Copyright (c) 2023, Cisco Systems, Inc. and/or its affiliates.
# All rights reserved.
# See LICENSE file in this distribution.
# SPDX-License-Identifier: Apache-2.0

""" Test Control Client """

import json
import urllib.parse as url_parse
from uuid import uuid4

import pytest
import responses
from responses import matchers

from tiedie.api.auth import ApiKeyAuthenticator, CertificateAuthenticator
from tiedie.api.control_client import ControlClient
from tiedie.models.ble import BleDataParameter
from tiedie.models.requests import SdfModel
from tiedie.models.responses import DataAppRegistration, Event
from tiedie.models.scim import (BleExtension, Device, PairingJustWorks,
                                PairingPassKey)


@pytest.fixture(name="mock_server")
def mocked_responses():
    """Mocked responses fixture"""
    with responses.RequestsMock() as rsps:
        yield rsps


@pytest.fixture(scope="module")
def api_key_authenticator():
    """API Key Authenticator fixture"""
    return ApiKeyAuthenticator(
        app_id="onboarding_app",
        ca_file_path="client_ca_path",
        api_key=str(uuid4())
    )


@pytest.fixture(scope="module")
def certificate_authenticator():
    """Certificate Authenticator fixture"""
    return CertificateAuthenticator(
        ca_file_path="",
        cert_path="",
        key_path=""
    )


@pytest.fixture(name="control_client",
                scope="module",
                params=['api_key_authenticator', 'certificate_authenticator'])
def mock_control_client(request: pytest.FixtureRequest):
    """ Mocked control client """
    return ControlClient(
        base_url="https://control.example.com/nipc",
        authenticator=request.getfixturevalue(request.param)
    )


def test_connect(mock_server: responses.RequestsMock,
                 control_client: ControlClient):
    """ Test connect """

    device_id = str(uuid4())

    body = json.dumps({
        "id": device_id,
        "sdfProtocolMap": {
            "ble": {
                "services": [
                    {
                        "serviceID": "1800",
                        "characteristics": [
                            {
                                "characteristicID": "2a00",
                                "flags": [
                                    "read",
                                    "write"
                                ],
                                "descriptors": [
                                    {
                                        "descriptorID": "2a10"
                                    }
                                ]
                            },
                            {
                                "characteristicID": "2a01",
                                "flags": [
                                    "read"
                                ],
                                "descriptors": [
                                    {
                                        "descriptorID": "2a11"
                                    }
                                ]
                            },
                            {
                                "characteristicID": "2a04",
                                "flags": [
                                    "read",
                                    "notify"
                                ],
                                "descriptors": [
                                    {
                                        "descriptorID": "2a14"
                                    }
                                ]
                            },
                            {
                                "characteristicID": "2aa6",
                                "flags": [
                                    "read"
                                ],
                                "descriptors": [
                                    {
                                        "descriptorID": "2a16"
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
        }
    }, separators=(',', ':'))

    # Only mock the default connect request (no services/bonding)
    mock_server.post(
        f"https://control.example.com/nipc/devices/{device_id}/connections",
        body=body,
        status=200,
        match=[
            matchers.json_params_matcher({
                "sdfProtocolMap": {
                    "ble": {}
                },
                "retries": 3,
                "retryMultipleAPs": True,
            }),
        ],
        content_type="application/nipc+json",
    )

    device = Device(
        display_name="BLE Monitor",
        active=False,
        device_id=device_id,
        ble_extension=BleExtension(
            device_mac_address="AA:BB:CC:11:22:33",
            is_random=False,
            version_support=["4.1", "4.2", "5.0", "5.1", "5.2", "5.3"],
            pairing_pass_key=PairingPassKey(key=123456),
            pairing_just_works=PairingJustWorks(key=0),
        )
    )

    response = control_client.connect(device)

    assert response.http and response.http.status_code == 200
    # Check if response is successful, body must be present for success
    if response.is_success:
        assert response.body is not None
        assert isinstance(response.body[0], BleDataParameter)
        assert isinstance(response.body[1], BleDataParameter)
        assert isinstance(response.body[2], BleDataParameter)
        assert isinstance(response.body[3], BleDataParameter)
        assert response.body[0].service_id == "1800"
        assert response.body[0].characteristic_id == "2a00"
        assert response.body[0].flags == ["read", "write"]
        assert response.body[1].service_id == "1800"
        assert response.body[1].characteristic_id == "2a01"
        assert response.body[1].flags == ["read"]
        assert response.body[2].service_id == "1800"
        assert response.body[2].characteristic_id == "2a04"
        assert response.body[2].flags == ["read", "notify"]
        assert response.body[3].service_id == "1800"
        assert response.body[3].characteristic_id == "2aa6"
        assert response.body[3].flags == ["read"]
    else:
        assert response.body is None


def test_disconnect(mock_server: responses.RequestsMock,
                    control_client: ControlClient):
    """ Test disconnect """

    device_id = str(uuid4())

    body = json.dumps({
        "id": device_id
    }, separators=(',', ':'))

    mock_server.delete(
        f"https://control.example.com/nipc/devices/{device_id}/connections",
        body=body,
        status=200,
        content_type="application/nipc+json",
    )

    device = Device(
        display_name="BLE Monitor",
        active=False,
        device_id=device_id,
        ble_extension=BleExtension(
            device_mac_address="AA:BB:CC:11:22:33",
            is_random=False,
            version_support=["4.1", "4.2", "5.0", "5.1", "5.2", "5.3"],
            pairing_pass_key=PairingPassKey(key=123456)
        )
    )

    response = control_client.disconnect(device)

    assert response.http and response.http.status_code == 200
    if response.is_success:
        assert response.body is not None


def test_discovery(mock_server: responses.RequestsMock,
                   control_client: ControlClient):
    """ Test Discovery """

    device_id = str(uuid4())

    body = json.dumps({
        "sdfProtocolMap": {
            "ble": {
                "services": [
                    {
                        "serviceID": "1800",
                        "characteristics": [
                            {
                                "characteristicID": "2a00",
                                "flags": [
                                    "read",
                                    "write"
                                ],
                                "descriptors": [
                                    {
                                        "descriptorID": "2a10"
                                    }
                                ]
                            },
                            {
                                "characteristicID": "2a01",
                                "flags": [
                                    "read"
                                ],
                                "descriptors": [
                                    {
                                        "descriptorID": "2a11"
                                    }
                                ]
                            },
                            {
                                "characteristicID": "2a04",
                                "flags": [
                                    "read",
                                    "notify"
                                ],
                                "descriptors": [
                                    {
                                        "descriptorID": "2a14"
                                    }
                                ]
                            },
                            {
                                "characteristicID": "2aa6",
                                "flags": [
                                    "read"
                                ],
                                "descriptors": [
                                    {
                                        "descriptorID": "2a16"
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
        }
    }, separators=(',', ':'))

    # Discovery uses PUT and /connections endpoint
    mock_server.put(
        f"https://control.example.com/nipc/devices/{device_id}/connections",
        body=body,
        status=200,
        match=[
            matchers.json_params_matcher({
                "sdfProtocolMap": {
                    "ble": {}
                },
                "retries": 3,
                "retryMultipleAPs": True
            }),
        ],
        content_type="application/nipc+json",
    )

    device = Device(
        display_name="BLE Monitor",
        active=False,
        device_id=device_id,
        ble_extension=BleExtension(
            device_mac_address="AA:BB:CC:11:22:33",
            is_random=False,
            version_support=["4.1", "4.2", "5.0", "5.1", "5.2", "5.3"],
            pairing_pass_key=PairingPassKey(key=123456)
        )
    )

    response = control_client.discover(device)

    assert response.http and response.http.status_code == 200
    if response.is_success:
        assert response.body is not None
        assert isinstance(response.body[0], BleDataParameter)
        assert isinstance(response.body[1], BleDataParameter)
        assert isinstance(response.body[2], BleDataParameter)
        assert isinstance(response.body[3], BleDataParameter)
        assert response.body[0].service_id == "1800"
        assert response.body[0].characteristic_id == "2a00"
        assert response.body[0].flags == ["read", "write"]
        assert response.body[1].service_id == "1800"
        assert response.body[1].characteristic_id == "2a01"
        assert response.body[1].flags == ["read"]
        assert response.body[2].service_id == "1800"
        assert response.body[2].characteristic_id == "2a04"
        assert response.body[2].flags == ["read", "notify"]
        assert response.body[3].service_id == "1800"
        assert response.body[3].characteristic_id == "2aa6"
        assert response.body[3].flags == ["read"]
    else:
        assert response.body is None


def test_read(mock_server: responses.RequestsMock,
              control_client: ControlClient):
    """ Test read """

    device_id = str(uuid4())

    body = json.dumps({
        "value": "00001111"
    }, separators=(',', ':'))

    # Remove 'id' from expected request body
    mock_server.post(
        f"https://control.example.com/nipc/extensions/{device_id}/properties/read",
        body=body,
        status=200,
        match=[
            matchers.json_params_matcher({
                "sdfProtocolMap": {
                    "ble": {
                        "serviceID": "1800",
                        "characteristicID": "2a00"
                    }
                }
            }),
        ],
        content_type="application/nipc+json",
    )

    device = Device(
        display_name="BLE Monitor",
        active=False,
        device_id=device_id,
        ble_extension=BleExtension(
            device_mac_address="AA:BB:CC:11:22:33",
            is_random=False,
            version_support=["4.1", "4.2", "5.0", "5.1", "5.2", "5.3"],
            pairing_pass_key=PairingPassKey(key=123456)
        )
    )

    response = control_client.read(device,
        service_id="1800",
        characteristic_id="2a00"
    )

    assert response.http and response.http.status_code == 200
    if response.is_success:
        assert response.body is not None
        assert response.body.value == "00001111"


def test_write(mock_server: responses.RequestsMock,
               control_client: ControlClient):
    """ Test write """

    device_id = str(uuid4())

    body = json.dumps({
        "value": "00001111"
    }, separators=(',', ':'))

    # Remove 'id' from expected request body
    mock_server.post(
        f"https://control.example.com/nipc/extensions/{device_id}/properties/write",
        body=body,
        status=200,
        match=[
            matchers.json_params_matcher({
                "value": "00001111",
                "sdfProtocolMap": {
                    "ble": {
                        "serviceID": "1800",
                        "characteristicID": "2a00"
                    }
                }
            }),
        ],
        content_type="application/nipc+json",
    )

    device = Device(
        display_name="BLE Monitor",
        active=False,
        device_id=device_id,
        ble_extension=BleExtension(
            device_mac_address="AA:BB:CC:11:22:33",
            is_random=False,
            version_support=["4.1", "4.2", "5.0", "5.1", "5.2", "5.3"],
            pairing_pass_key=PairingPassKey(key=123456)
        )
    )

    response = control_client.write(
        device,
        service_id="1800",
        characteristic_id="2a00",
        value="00001111")

    assert response.http and response.http.status_code == 200
    if response.is_success:
        assert response.body is not None
        assert response.body.value == "00001111"


def test_register_sdf_model(mock_server: responses.RequestsMock, control_client: ControlClient):
    """Test registering an SDF model"""
    sdf_model_data = {
        "namespace": {"thermometer": "https://example.com/thermometer"},
        "defaultNamespace": "thermometer",
        "sdfObject": {
            "healthsensor": {
                "sdfProperty": {
                    "temperature": {
                        "observable": True,
                        "readable": True,
                        "writable": True,
                        "sdfProtocolMap": {
                            "ble": {
                                "serviceID": "1809",
                                "characteristicID": "2A1C"
                            }
                        }
                    }
                }
            }
        }
    }
    body = json.dumps([{
        "sdfName": "https://example.com/thermometer#/sdfObject/healthsensor"
    }], separators=(',', ':'))
    mock_server.post(
        "https://control.example.com/nipc/registrations/models",
        body=body,
        status=200,
        match=[matchers.json_params_matcher(sdf_model_data)],
        content_type="application/nipc+json",
    )
    sdf_model = SdfModel(**sdf_model_data)
    response = control_client.register_sdf_model(sdf_model)

    assert response.http and response.http.status_code == 200
    if response.is_success:
        assert response.body is not None
        assert len(response.body.root) == 1
        expected_sdf_name = "https://example.com/thermometer#/sdfObject/healthsensor"
        assert response.body.root[0].sdf_name == expected_sdf_name


def test_property_read_api(mock_server: responses.RequestsMock, control_client: ControlClient):
    """Test reading a property using the property API"""
    device_id = str(uuid4())
    property_ref = "https://example.com/thermometer#/sdfObject/healthsensor/sdfProperty/temperature"
    body = json.dumps([{
        "property": property_ref,
        "value": "dGVzdA=="
    }], separators=(',', ':'))
    encoded_property_ref = url_parse.quote(property_ref)
    mock_server.get(
        f"https://control.example.com/nipc/devices/{device_id}/properties"
        f"?propertyName={encoded_property_ref}",
        body=body,
        status=200,
        content_type="application/nipc+json",
    )
    response = control_client.read_property(device_id, property_ref)

    assert response.http and response.http.status_code == 200
    if response.is_success:
        assert response.body is not None
        assert len(response.body.root) == 1
        assert response.body.root[0].property == property_ref
        assert response.body.root[0].value == b"test"


def test_property_write_api(mock_server: responses.RequestsMock, control_client: ControlClient):
    """Test writing a property using the property API"""
    device_id = str(uuid4())
    property_ref = "https://example.com/thermometer#/sdfObject/healthsensor/sdfProperty/temperature"
    value = "dGVzdA=="
    req_body = [
        {
            "property": property_ref,
            "value": value
        }
    ]
    resp_body = json.dumps([{
        "status": 200
    }], separators=(',', ':'))
    mock_server.put(
        f"https://control.example.com/nipc/devices/{device_id}/properties",
        body=resp_body,
        status=200,
        match=[matchers.json_params_matcher(req_body)],
        content_type="application/nipc+json",
    )
    response = control_client.write_property(device_id, property_ref, value)

    assert response.http and response.http.status_code == 200
    if response.is_success:
        assert response.body is not None
        assert len(response.body.root) == 1
        assert response.body.root[0].status == 200


def test_register_data_app(mock_server: responses.RequestsMock, control_client: ControlClient):
    """Test registering a data app"""
    data_app_id = str(uuid4())
    event_ref = "https://example.com/thermometer#/sdfObject/healthsensor/sdfEvent/isPresent"
    req_body = {
        "events": [{"event": event_ref}],
        "mqttClient": True
    }
    resp_body = json.dumps(req_body, separators=(',', ':'))
    mock_server.post(
        f"https://control.example.com/nipc/registrations/data-apps?dataAppId={data_app_id}",
        body=resp_body,
        status=200,
        match=[matchers.json_params_matcher(req_body)],
        content_type="application/nipc+json",
    )
    data_app = DataAppRegistration(
        events=[Event(event=event_ref)],
        mqtt_client=True,
    )
    response = control_client.create_data_app(data_app_id, data_app)

    assert response.http and response.http.status_code == 200
    if response.is_success:
        assert response.body is not None
        assert response.body.events[0].event == event_ref
        assert response.body.mqtt_client is True


def test_enable_event(mock_server: responses.RequestsMock, control_client: ControlClient):
    """Test enabling an event"""
    device_id = str(uuid4())
    event_ref = "https://example.com/thermometer#/sdfObject/healthsensor/sdfEvent/isPresent"
    instance_id = str(uuid4())

    encoded_event_ref = url_parse.quote(event_ref)
    location_header = (
        f"https://control.example.com/nipc/devices/{device_id}/events"
        f"?instanceId={instance_id}"
    )
    post_url = (
        f"https://control.example.com/nipc/devices/{device_id}/events"
        f"?eventName={encoded_event_ref}"
    )
    mock_server.post(
        post_url,
        body="",
        status=200,
        headers={"Location": location_header},
        content_type="application/nipc+json",
    )
    response = control_client.enable_event(device_id, event_ref)

    assert response.http and response.http.status_code == 200
    if response.is_success:
        assert response.body == instance_id
