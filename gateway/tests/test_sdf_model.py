# Copyright (c) 2023-2025, Cisco Systems, Inc. and/or its affiliates.
# All rights reserved.
# See LICENSE file in this distribution.
# SPDX-License-Identifier: Apache-2.0
"""
Unit tests for SDF model registration and management (NIPC draft-12)
"""
import uuid
import pytest
from flask import Flask
from flask.testing import FlaskClient
from testcontainers.postgres import PostgresContainer
from app_factory import create_app
from database import db
from models import OnboardingAppKey
# pylint: disable-next=unused-import
from scim_fdo import FDOExtension
# pylint: disable-next=unused-import
from scim_ethermab import EtherMABExtension


@pytest.fixture(name="postgres")
def fixture_postgres():
    """Fixture for Postgres test container."""
    with PostgresContainer("postgres:13.1") as p:
        yield p


@pytest.fixture(name="app")
def fixture_app(postgres: PostgresContainer):
    """Fixture for Flask app with test DB."""
    app = create_app(postgres.get_connection_url())
    with app.app_context():
        db.create_all()
    yield app


@pytest.fixture(name="client")
def fixture_client(app: Flask) -> FlaskClient:
    """Fixture for Flask test client."""
    return app.test_client()


@pytest.fixture(name="api_key")
def fixture_api_key(app):
    """Fixture for onboarding app key."""
    with app.app_context():
        key = uuid.uuid4()
        authkey = OnboardingAppKey("onboarding-app", str(key))
        db.session.add(authkey)
        db.session.commit()
        yield key


@pytest.fixture(name="control_api_key")
def fixture_endpoint_app_token(client: FlaskClient, api_key: str):
    """Fixture for endpoint app token."""
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


def sample_sdf_model():
    """Return a sample SDF model dict."""
    return {
        "namespace": {"thermometer": "https://example.com/thermometer"},
        "defaultNamespace": "thermometer",
        "sdfObject": {
            "healthsensor": {
                "sdfProperty": {
                    "temperature": {
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


def test_register_and_manage_sdf_model(client: FlaskClient, control_api_key: str) -> None:
    """Test SDF model registration, duplicate, list, get, update, and delete operations."""

    sdf_headers = {
        "x-api-key": control_api_key,
        "Content-Type": "application/json"
    }
    # Register
    resp = client.post("/nipc/registrations/models",
                       json=sample_sdf_model(), headers=sdf_headers)
    assert resp.status_code == 200
    assert resp.json is not None
    assert len(resp.json) == 1
    assert isinstance(resp.json, list)
    assert "sdfName" in resp.json[0]
    sdf_name = resp.json[0]["sdfName"]

    # Duplicate registration should fail
    resp2 = client.post("/nipc/registrations/models",
                        json=sample_sdf_model(), headers=sdf_headers)
    assert resp2.status_code == 409
    assert resp2.json is not None
    print("Duplicate registration error response:", resp2.json)
    assert resp2.json["type"] == ("https://www.iana.org/assignments/"
                                 "nipc-problem-types#sdf-model-already-registered")
    assert resp2.json["status"] == 409

    # List models
    resp3 = client.get("/nipc/registrations/models", headers=sdf_headers)
    assert resp3.status_code == 200
    assert resp3.json is not None
    assert isinstance(resp3.json, list)
    assert any(model["sdfName"] == sdf_name for model in resp3.json)

    # Get model by name (URL-encoded as query parameter)
    resp4 = client.get(
        "/nipc/registrations/models",
        query_string={"sdfName": sdf_name},
        headers=sdf_headers)
    assert resp4.status_code == 200
    assert resp4.json is not None
    assert resp4.json["sdfObject"] == sample_sdf_model()["sdfObject"]

    # Update model (valid update: add a property, not change namespace)
    updated = sample_sdf_model()
    updated["sdfObject"]["healthsensor"]["sdfProperty"]["humidity"] = {
        "sdfProtocolMap": {
            "ble": {
                "serviceID": "1809",
                "characteristicID": "2A1D"
            }
        }
    }
    resp5 = client.put(
        "/nipc/registrations/models",
        query_string={"sdfName": sdf_name},
        json=updated,
        headers=sdf_headers
    )
    assert resp5.status_code == 200
    # Confirm update
    resp6 = client.get(
        "/nipc/registrations/models",
        query_string={"sdfName": sdf_name},
        headers=sdf_headers)
    assert resp6.status_code == 200
    assert resp6.json is not None
    print(resp6.json)
    assert "humidity" in resp6.json["sdfObject"]["healthsensor"]["sdfProperty"]

    # Attempt to update namespace (should fail)
    forbidden_update = sample_sdf_model()
    forbidden_update["namespace"] = {
        "thermometer": "https://malicious.com/other"}
    resp_forbidden = client.put(
        "/nipc/registrations/models",
        query_string={"sdfName": sdf_name},
        json=forbidden_update,
        headers=sdf_headers)
    assert resp_forbidden.status_code == 400
    assert resp_forbidden.json is not None
    print("Namespace update error response:", resp_forbidden.json)
    assert resp_forbidden.json["type"] == ("https://www.iana.org/assignments/"
                                         "nipc-problem-types#invalid-sdf-url")
    assert resp_forbidden.json["status"] == 400

    # Attempt to update defaultNamespace (should fail)
    forbidden_update2 = sample_sdf_model()
    forbidden_update2["defaultNamespace"] = "other"
    resp_forbidden2 = client.put(
        "/nipc/registrations/models",
        query_string={"sdfName": sdf_name},
        json=forbidden_update2,
        headers=sdf_headers)
    assert resp_forbidden2.status_code == 400
    assert resp_forbidden2.json is not None
    assert resp_forbidden2.json["type"] == \
        "https://www.iana.org/assignments/nipc-problem-types#invalid-sdf-url"
    assert resp_forbidden2.json["status"] == 400

    # Delete model
    resp7 = client.delete(
        "/nipc/registrations/models",
        query_string={"sdfName": sdf_name},
        headers=sdf_headers)
    assert resp7.status_code == 200
    # Confirm deletion
    resp8 = client.get(
        "/nipc/registrations/models",
        query_string={"sdfName": sdf_name},
        headers=sdf_headers)
    assert resp8.status_code == 404
    assert resp8.json is not None
    assert resp8.json["type"] == \
        "https://www.iana.org/assignments/nipc-problem-types#invalid-sdf-url"
    assert resp8.json["status"] == 404
