# Copyright (c) 2023, Cisco Systems, Inc. and/or its affiliates.
# All rights reserved.
# See LICENSE file in this distribution.
# SPDX-License-Identifier: Apache-2.0

"""
Test SCIM server implementation
"""

import uuid
from flask import Flask
from flask.testing import FlaskClient
import pytest
from testcontainers.postgres import PostgresContainer
from app_factory import create_app
from models import OnboardingAppKey
from database import db


@pytest.fixture(name="postgres")
def fixture_postgres():
    """ Postgres container """
    with PostgresContainer("postgres:13.1") as p:
        yield p


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

def test_create_device(client: FlaskClient, api_key: str):
    """ Test POST Device """
    response = client.post(
        "/scim/v2/Devices",
        json={
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Device",
                "urn:ietf:params:scim:schemas:extension:ble:2.0:Device"],
            "deviceDisplayName": "BLE Heart Monitor",
            "adminState": True,
            "urn:ietf:params:scim:schemas:extension:ble:2.0:Device" : {       
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
    print(response.json)
    assert response.json["id"] is not None
    assert response.json["meta"] is not None
    assert response.json["schemas"] == [
        'urn:ietf:params:scim:schemas:core:2.0:Device',
        'urn:ietf:params:scim:schemas:extension:ble:2.0:Device',
        'urn:ietf:params:scim:schemas:extension:endpointAppsExt:2.0:Device'
    ]

def test_get_device(client: FlaskClient, api_key):
    """ Test GET device """
    device_id = uuid.uuid4()
    response = client.get(f"/scim/v2/Devices/{device_id}", headers={
        "x-api-key": api_key
    })

    assert response.status_code == 404

    response = client.post(
        "/scim/v2/Devices",
        json={
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Device",
                "urn:ietf:params:scim:schemas:extension:ble:2.0:Device"],
            "deviceDisplayName": "BLE Heart Monitor",
            "adminState": True,
            "urn:ietf:params:scim:schemas:extension:ble:2.0:Device" : {       
                "versionSupport": ["5.3"],
                "deviceMacAddress": "AA:BB:CC:11:22:33",
                "isRandom": False,
                "mobility": True  
            }
        }, headers={
            "x-api-key": api_key
        }
    )

    device_id = response.json["id"]

    response = client.get(f"/scim/v2/Devices/{device_id}", headers={
        "x-api-key": api_key
    })

    assert response.status_code == 200
    print(response.json)
    assert response.json["id"] == device_id
    assert response.json["meta"] is not None
