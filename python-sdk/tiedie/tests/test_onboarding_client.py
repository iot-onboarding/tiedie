# Copyright (c) 2023, Cisco Systems, Inc. and/or its affiliates.
# All rights reserved.
# See LICENSE file in this distribution.
# SPDX-License-Identifier: Apache-2.0

"""Test the Onboarding Client"""

import json
from uuid import uuid4
import pytest
import responses
from tiedie.api.onboarding_client import OnboardingClient
from tiedie.api.auth import ApiKeyAuthenticator, CertificateAuthenticator
from tiedie.models.scim import (
    AppCertificateInfo, BleExtension, Device, EndpointApp, EndpointAppType, PairingPassKey
)


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


@pytest.fixture(name="onboarding_client",
                scope="module",
                params=['api_key_authenticator', 'certificate_authenticator'])
def mock_onboarding_client(request):
    """ Mocked onboarding client """
    return OnboardingClient(
        base_url="https://onboarding.example.com/scim/v2",
        authenticator=request.getfixturevalue(request.param)
    )


def test_device_creation(mock_server: responses.RequestsMock,
                         onboarding_client: OnboardingClient):
    """ Test device creation """

    device_id = str(uuid4())

    mock_server.post(
        "https://onboarding.example.com/scim/v2/Devices",
        body=json.dumps({
            "deviceDisplayName": "BLE Monitor",
            "id": device_id,
            "adminState": False,
            "urn:ietf:params:scim:schemas:extension:ble:2.0:Device":
            {
                "versionSupport": ["4.1", "4.2", "5.0", "5.1", "5.2", "5.3"],
                "deviceMacAddress": "AA:BB:CC:11:22:33",
                "isRandom": False,
                "urn:ietf:params:scim:schemas:extension:pairingPassKey:2.0:Device":
                {"key": 123456},
                "pairingMethods":
                ["urn:ietf:params:scim:schemas:extension:pairingPassKey:2.0:Device"],
            },
            "schemas":
            [
                "urn:ietf:params:scim:schemas:core:2.0:Device",
                "urn:ietf:params:scim:schemas:extension:ble:2.0:Device",
            ],
        }, separators=(',', ':')),
        status=201,
        content_type="application/scim+json",
    )

    device = Device(
        device_display_name="BLE Monitor",
        admin_state=False,
        ble_extension=BleExtension(
            device_mac_address="AA:BB:CC:11:22:33",
            is_random=False,
            version_support=["4.1", "4.2", "5.0", "5.1", "5.2", "5.3"],
            pairing_pass_key=PairingPassKey(key=123456)
        )
    )

    response = onboarding_client.create_device(device)
    assert response.status_code == 201
    assert response.body is not None
    assert response.body.device_display_name == "BLE Monitor"
    assert response.body.device_id == device_id


def test_get_device(mock_server: responses.RequestsMock,
                    onboarding_client: OnboardingClient):
    """ Test get device """

    device_id = str(uuid4())

    mock_server.get(
        f"https://onboarding.example.com/scim/v2/Devices/{device_id}",
        body=json.dumps({
            "deviceDisplayName": "BLE Monitor",
            "id": device_id,
            "adminState": False,
            "urn:ietf:params:scim:schemas:extension:ble:2.0:Device":
            {
                "versionSupport": ["4.1", "4.2", "5.0", "5.1", "5.2", "5.3"],
                "deviceMacAddress": "AA:BB:CC:11:22:33",
                "isRandom": False,
                "urn:ietf:params:scim:schemas:extension:pairingPassKey:2.0:Device":
                {"key": 123456},
                "pairingMethods":
                ["urn:ietf:params:scim:schemas:extension:pairingPassKey:2.0:Device"],
            },
            "schemas":
            [
                "urn:ietf:params:scim:schemas:core:2.0:Device",
                "urn:ietf:params:scim:schemas:extension:ble:2.0:Device",
            ],
        }, separators=(',', ':')),
        status=200,
        content_type="application/scim+json",
    )

    response = onboarding_client.get_device(device_id)
    assert response.status_code == 200
    assert response.body.device_display_name == "BLE Monitor"
    assert response.body.device_id == device_id


def test_get_devices(mock_server: responses.RequestsMock,
                     onboarding_client: OnboardingClient):
    """ Test get devices """

    device_id_1 = str(uuid4())
    device_id_2 = str(uuid4())

    mock_server.get(
        "https://onboarding.example.com/scim/v2/Devices",
        body=json.dumps({
            "totalResults": 2,
            "itemsPerPage": 2,
            "startIndex": 1,
            "Resources": [
                {
                    "deviceDisplayName": "BLE Monitor",
                    "id": device_id_1,
                    "adminState": False,
                    "urn:ietf:params:scim:schemas:extension:ble:2.0:Device":
                    {
                        "versionSupport": ["4.1", "4.2", "5.0", "5.1", "5.2", "5.3"],
                        "deviceMacAddress": "AA:BB:CC:11:22:33",
                        "isRandom": False,
                        "urn:ietf:params:scim:schemas:extension:pairingPassKey:2.0:Device":
                        {"key": 123456},
                        "pairingMethods":
                        ["urn:ietf:params:scim:schemas:extension:pairingPassKey:2.0:Device"],
                    },
                    "schemas":
                    [
                        "urn:ietf:params:scim:schemas:core:2.0:Device",
                        "urn:ietf:params:scim:schemas:extension:ble:2.0:Device",
                    ],
                },
                {
                    "deviceDisplayName": "Zigbee Monitor",
                    "id": device_id_2,
                    "adminState": False,
                    "urn:ietf:params:scim:schemas:extension:zigbee:2.0:Device": {
                        "versionSupport": [
                            "3.0"
                        ],
                        "deviceEui64Address": "50325FFFFEE76728"
                    },
                    "schemas": [
                        "urn:ietf:params:scim:schemas:core:2.0:Device",
                        "urn:ietf:params:scim:schemas:extension:zigbee:2.0:Device"
                    ]
                }
            ]
        }),
        status=200,
        content_type="application/scim+json",
    )

    response = onboarding_client.get_devices()

    assert response.status_code == 200
    assert response.body.total_results == 2
    assert response.body.items_per_page == 2
    assert response.body.start_index == 1
    assert len(response.body.resources) == 2
    assert response.body.resources[0].device_display_name == "BLE Monitor"
    assert response.body.resources[0].device_id == device_id_1
    assert response.body.resources[1].device_display_name == "Zigbee Monitor"
    assert response.body.resources[1].device_id == device_id_2


def test_delete_device(mock_server: responses.RequestsMock,
                       onboarding_client: OnboardingClient):
    """ Test delete device """
    device_id = str(uuid4())

    mock_server.delete(
        f"https://onboarding.example.com/scim/v2/Devices/{device_id}",
        status=204,
        content_type="application/scim+json",
    )

    response = onboarding_client.delete_device(device_id)
    assert response.status_code == 204
    assert response.message == "No Content"


def test_create_endpoint_apps(mock_server: responses.RequestsMock,
                              onboarding_client: OnboardingClient):
    """ Test create endpoint apps """
    app_id = str(uuid4())
    client_token = str(uuid4())

    mock_server.post(
        "https://onboarding.example.com/scim/v2/EndpointApps",
        body=json.dumps({
            "id": app_id,
            "applicationName": "control-app",
            "applicationType": "deviceControl",
            "clientToken": client_token,
        }),
        status=201,
        content_type="application/scim+json",
    )

    response = onboarding_client.create_endpoint_app(EndpointApp(
        application_name="control-app",
        application_type=EndpointAppType.DEVICE_CONTROL
    ))

    assert response.status_code == 201
    assert response.body.application_name == "control-app"
    assert response.body.application_type == "deviceControl"
    assert response.body.application_id == app_id
    assert response.body.client_token == client_token

    mock_server.post(
        "https://onboarding.example.com/scim/v2/EndpointApps",
        body=json.dumps({
            "id": app_id,
            "applicationName": "data-app",
            "applicationType": "telemetry",
            "certificateInfo": {
                "rootCN": "Root CA",
                "subjectName": "telemetry.example.com"
            }
        }),
        status=201,
        content_type="application/scim+json",
    )

    response = onboarding_client.create_endpoint_app(EndpointApp(
        application_name="data-app",
        application_type=EndpointAppType.TELEMETRY,
        certificate_info=AppCertificateInfo(
            root_cn="Root CA",
            subject_name="telemetry.example.com"
        )
    ))

    assert response.status_code == 201
    assert response.body.application_name == "data-app"
    assert response.body.application_type == "telemetry"
    assert response.body.application_id == app_id


def test_get_endpoint_app(mock_server: responses.RequestsMock,
                          onboarding_client: OnboardingClient):
    """ Test get endpoint app """

    app_id = str(uuid4())

    mock_server.get(
        f"https://onboarding.example.com/scim/v2/EndpointApps/{app_id}",
        body=json.dumps({
            "id": app_id,
            "applicationName": "control-app",
            "applicationType": "deviceControl",
            "clientToken": str(uuid4()),
        }),
        status=200,
        content_type="application/scim+json",
    )

    response = onboarding_client.get_endpoint_app(app_id)

    assert response.status_code == 200
    assert response.body.application_name == "control-app"
    assert response.body.application_type == "deviceControl"
    assert response.body.application_id == app_id


def test_get_endpoint_apps(mock_server: responses.RequestsMock,
                           onboarding_client: OnboardingClient):
    """ Test get endpoint apps """

    app_id_1 = str(uuid4())
    app_id_2 = str(uuid4())

    mock_server.get(
        "https://onboarding.example.com/scim/v2/EndpointApps",
        body=json.dumps({
            "totalResults": 2,
            "itemsPerPage": 2,
            "startIndex": 1,
            "Resources": [
                {
                    "id": app_id_1,
                    "applicationName": "control-app",
                    "applicationType": "deviceControl",
                    "clientToken": str(uuid4()),
                },
                {
                    "id": app_id_2,
                    "applicationName": "data-app",
                    "applicationType": "telemetry",
                    "certificateInfo": {
                        "rootCN": "Root CA",
                        "subjectName": "telemetry.example.com"
                    }
                }
            ]
        }),
        status=200,
        content_type="application/scim+json",
    )

    response = onboarding_client.get_endpoint_apps()

    assert response.status_code == 200
    assert response.body.total_results == 2
    assert response.body.items_per_page == 2
    assert response.body.start_index == 1
    assert len(response.body.resources) == 2
    assert response.body.resources[0].application_name == "control-app"
    assert response.body.resources[0].application_type == "deviceControl"
    assert response.body.resources[0].application_id == app_id_1
    assert response.body.resources[1].application_name == "data-app"
    assert response.body.resources[1].application_type == "telemetry"
    assert response.body.resources[1].application_id == app_id_2
