# Copyright (c) 2023, Cisco Systems, Inc. and/or its affiliates.
# All rights reserved.
# See LICENSE file in this distribution.
# SPDX-License-Identifier: Apache-2.0
# pylint: disable=consider-using-with

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
# pylint: disable-next=unused-import
from scim_fdo import FDOExtension
# pylint: disable-next=unused-import
from scim_ethermab import EtherMABExtension
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
    print(response.json)
    assert response.json["id"] is not None
    assert response.json["meta"] is not None
    assert response.json["schemas"] == [
        'urn:ietf:params:scim:schemas:core:2.0:Device',
        'urn:ietf:params:scim:schemas:extension:ble:2.0:Device',
    ]
    assert "urn:ietf:params:scim:schemas:extension:ble:2.0:Device" in response.json


def test_unsupported_schema(client: FlaskClient, api_key: str):
    """ Test POST Device """
    response = client.post(
        "/scim/v2/Devices",
        json={
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Device",
                        "urn:ietf:params:scim:schemas:extension:ble:2.0:Device"
                        "urn:ietf:params:scim:schemas:extension:nosuchshema:2.0:Device"],
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
    print(response.json)
    assert response.status_code == 501


def test_get_device(client: FlaskClient, api_key):
    """ Test GET device """
    device_id = uuid.uuid4()
    response = client.get(f"/scim/v2/Devices/{device_id}", headers={
        "x-api-key": api_key
    })

    assert response.status_code == 404

    response = client.get("/scim/v2/Devices", headers={
        "x-api-key": api_key
    })

    assert response.status_code == 200
    print(response.json)
    assert response.json["totalResults"] == 0
    assert response.json["schemas"] == [
        "urn:ietf:params:scim:api:messages:2.0:ListResponse"]
    assert len(response.json["Resources"]) == 0

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

    device_id = response.json["id"]

    response = client.get(f"/scim/v2/Devices/{device_id}", headers={
        "x-api-key": api_key
    })

    assert response.status_code == 200
    print(response.json)
    assert response.json["id"] == device_id
    assert response.json["meta"] is not None
    assert "urn:ietf:params:scim:schemas:extension:ble:2.0:Device" in response.json

    response = client.get("/scim/v2/Devices", headers={
        "x-api-key": api_key
    })

    assert response.status_code == 200
    print(response.json)
    assert response.json["totalResults"] == 1
    assert response.json["schemas"] == [
        "urn:ietf:params:scim:api:messages:2.0:ListResponse"]
    assert len(response.json["Resources"]) == 1
    assert response.json["Resources"][0]["id"] == device_id

    # Test filter
    response = client.get(
        "/scim/v2/Devices?filter=deviceMacAddress eq \"AA:BB:CC:11:22:33\"",
        headers={
            "x-api-key": api_key
        })

    print(response.json)
    assert response.status_code == 200
    assert response.json["totalResults"] == 1
    assert response.json["Resources"][0]["id"] == device_id
    assert "urn:ietf:params:scim:schemas:extension:ble:2.0:Device" in response.json[
        "Resources"][0]


def test_delete_device(client: FlaskClient, api_key):
    """ Test DELETE device """
    device_id = uuid.uuid4()
    response = client.delete(f"/scim/v2/Devices/{device_id}", headers={
        "x-api-key": api_key
    })

    assert response.status_code == 404

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

    device_id = response.json["id"]

    response = client.delete(f"/scim/v2/Devices/{device_id}", headers={
        "x-api-key": api_key
    })

    assert response.status_code == 204

    response = client.get(f"/scim/v2/Devices/{device_id}", headers={
        "x-api-key": api_key
    })

    assert response.status_code == 404

    response = client.get("/scim/v2/Devices", headers={
        "x-api-key": api_key
    })

    assert response.status_code == 200
    print(response.json)
    assert response.json["totalResults"] == 0
    assert response.json["schemas"] == [
        "urn:ietf:params:scim:api:messages:2.0:ListResponse"]
    assert len(response.json["Resources"]) == 0


def test_create_mab_device(client: FlaskClient, api_key: str):
    """ Test POST Device """
    response = client.post(
        "/scim/v2/Devices",
        json={
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Device",
                        "urn:ietf:params:scim:schemas:extension:ethernet-mab:2.0:Device"],
            "displayName": "Generic MAB Device",
            "active": True,
            "urn:ietf:params:scim:schemas:extension:ethernet-mab:2.0:Device": {
                "deviceMacAddress": "AA:BB:CC:11:22:33"
            }
        }, headers={
            "x-api-key": api_key
        }
    )

    assert response.status_code == 201
    print(response.json)
    assert response.json["id"] is not None
    assert response.json["meta"] is not None
    assert "urn:ietf:params:scim:schemas:extension:ethernet-mab:2.0:Device" in response.json
    assert response.json["schemas"] == [
        'urn:ietf:params:scim:schemas:core:2.0:Device',
        'urn:ietf:params:scim:schemas:extension:ethernet-mab:2.0:Device'
    ]


def test_get_mab_device(client: FlaskClient, api_key):
    """ Test GET device """
    device_id = uuid.uuid4()
    response = client.get(f"/scim/v2/Devices/{device_id}", headers={
        "x-api-key": api_key
    })

    assert response.status_code == 404

    response = client.get("/scim/v2/Devices", headers={
        "x-api-key": api_key
    })

    assert response.status_code == 200
    assert response.json["totalResults"] == 0
    assert response.json["schemas"] == [
        "urn:ietf:params:scim:api:messages:2.0:ListResponse"]
    assert len(response.json["Resources"]) == 0

    response = client.post(
        "/scim/v2/Devices",
        json={
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Device",
                        "urn:ietf:params:scim:schemas:extension:ethernet-mab:2.0:Device"],
            "displayName": "Generic MAB Device",
            "active": True,
            "urn:ietf:params:scim:schemas:extension:ethernet-mab:2.0:Device": {
                "deviceMacAddress": "AA:BB:CC:00:22:33"
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

    assert response.json["id"] == device_id
    assert response.json["meta"] is not None
    assert "urn:ietf:params:scim:schemas:extension:ethernet-mab:2.0:Device" in response.json

    response = client.get("/scim/v2/Devices", headers={
        "x-api-key": api_key
    })

    assert response.status_code == 200
    print(response.json)
    assert response.json["totalResults"] == 1
    assert response.json["schemas"] == [
        "urn:ietf:params:scim:api:messages:2.0:ListResponse"]
    assert len(response.json["Resources"]) == 1
    assert response.json["Resources"][0]["id"] == device_id

    # Test filter
    response = client.get(
        "/scim/v2/Devices?filter=deviceMacAddress eq \"AA:BB:CC:00:22:33\"",
        headers={
            "x-api-key": api_key
        })

    print(response.json)
    assert response.status_code == 200
    assert response.json["totalResults"] == 1
    assert response.json["Resources"][0]["id"] == device_id
    assert "urn:ietf:params:scim:schemas:extension:ethernet-mab:2.0:Device" \
        in response.json["Resources"][0]


def test_delete_mab_device(client: FlaskClient, api_key):
    """ Test DELETE device """
    device_id = uuid.uuid4()
    response = client.delete(f"/scim/v2/Devices/{device_id}", headers={
        "x-api-key": api_key
    })

    assert response.status_code == 404

    response = client.post(
        "/scim/v2/Devices",
        json={
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Device",
                        "urn:ietf:params:scim:schemas:extension:ethernet-mab:2.0:Device"],
            "displayName": "Generic MAB Device",
            "active": True,
            "urn:ietf:params:scim:schemas:extension:ethernet-mab:2.0:Device": {
                "deviceMacAddress": "AA:BB:CC:11:22:33"
            }
        }, headers={
            "x-api-key": api_key
        }
    )

    device_id = response.json["id"]

    response = client.delete(f"/scim/v2/Devices/{device_id}", headers={
        "x-api-key": api_key
    })

    assert response.status_code == 204

    response = client.get(f"/scim/v2/Devices/{device_id}", headers={
        "x-api-key": api_key
    })

    assert response.status_code == 404

    response = client.get("/scim/v2/Devices", headers={
        "x-api-key": api_key
    })

    assert response.status_code == 200
    print(response.json)
    assert response.json["totalResults"] == 0
    assert response.json["schemas"] == [
        "urn:ietf:params:scim:api:messages:2.0:ListResponse"]
    assert len(response.json["Resources"]) == 0


def test_create_fdo_device(client: FlaskClient, api_key: str):
    """ Test POST Device """

    voucher = open("tests/fdo-voucher.b64", encoding="utf-8").read()
    response = client.post(
        "/scim/v2/Devices",
        json={
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Device",
                        "urn:ietf:params:scim:schemas:extension:fido-device-onboard:2.0:Device"],
            "displayName": "Generic FDO Device",
            "active": True,
            "urn:ietf:params:scim:schemas:extension:fido-device-onboard:2.0:Device": {
                "fdoOwnerVoucher": voucher
            }
        }, headers={
            "x-api-key": api_key
        }
    )

    assert response.status_code in (200, 201)
    device_id = response.json["id"]

    response = client.get(f"/scim/v2/Devices/{device_id}", headers={
        "x-api-key": api_key
    })

    assert response.status_code == 200

    assert response.json["id"] == device_id
    assert response.json["meta"] is not None
    assert "urn:ietf:params:scim:schemas:extension:fido-device-onboard:2.0:Device" in response.json

    response = client.get("/scim/v2/Devices", headers={
        "x-api-key": api_key
    })

    assert response.status_code == 200
    print(response.json)
    assert response.json["totalResults"] == 1
    assert response.json["schemas"] == [
        "urn:ietf:params:scim:api:messages:2.0:ListResponse"]
    assert len(response.json["Resources"]) == 1
    assert response.json["Resources"][0]["id"] == device_id

    # Test filter
    response = client.get(
        "/scim/v2/Devices?filter=deviceMacAddress eq \"AA:BB:CC:00:22:33\"",
        headers={
            "x-api-key": api_key
        })

    print(response.json)
    assert response.status_code == 200
    assert response.json["totalResults"] == 0


def test_get_fdo_device(client: FlaskClient, api_key):
    """ Test GET device """
    device_id = uuid.uuid4()
    response = client.get(f"/scim/v2/Devices/{device_id}", headers={
        "x-api-key": api_key
    })

    assert response.status_code == 404

    response = client.get("/scim/v2/Devices", headers={
        "x-api-key": api_key
    })

    assert response.status_code == 200
    assert response.json["totalResults"] == 0
    assert response.json["schemas"] == [
        "urn:ietf:params:scim:api:messages:2.0:ListResponse"]
    assert len(response.json["Resources"]) == 0
    voucher = open("tests/fdo-voucher.b64", encoding="utf-8").read()

    response = client.post(
        "/scim/v2/Devices",
        json={
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Device",
                        "urn:ietf:params:scim:schemas:extension:fido-device-onboard:2.0:Device"],
            "displayName": "Generic MAB Device",
            "active": True,
            "urn:ietf:params:scim:schemas:extension:fido-device-onboard:2.0:Device": {
                "fdoOwnerVoucher": voucher
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

    assert response.json["id"] == device_id
    assert response.json["meta"] is not None
    assert "urn:ietf:params:scim:schemas:extension:fido-device-onboard:2.0:Device" in response.json

    response = client.get("/scim/v2/Devices", headers={
        "x-api-key": api_key
    })

    assert response.status_code == 200
    print(response.json)
    assert response.json["totalResults"] == 1
    assert response.json["schemas"] == [
        "urn:ietf:params:scim:api:messages:2.0:ListResponse"]
    assert len(response.json["Resources"]) == 1
    assert response.json["Resources"][0]["id"] == device_id

    # Test filter
    response = client.get(
        "/scim/v2/Devices?filter=deviceMacAddress eq \"AA:BB:CC:00:22:33\"",
        headers={
            "x-api-key": api_key
        })

    print(response.json)
    assert response.status_code == 200
    assert response.json["totalResults"] == 0


def test_delete_fdo_device(client: FlaskClient, api_key):
    """ Test DELETE device """
    device_id = uuid.uuid4()
    response = client.delete(f"/scim/v2/Devices/{device_id}", headers={
        "x-api-key": api_key
    })

    assert response.status_code == 404
    voucher = open("tests/fdo-voucher.b64", encoding="utf-8").read()

    response = client.post(
        "/scim/v2/Devices",
        json={
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Device",
                        "urn:ietf:params:scim:schemas:extension:fido-device-onboard:2.0:Device"],
            "displayName": "Generic FDO Device",
            "active": True,
            "urn:ietf:params:scim:schemas:extension:fido-device-onboard:2.0:Device": {
                "fdoOwnerVoucher": voucher
            }
        }, headers={
            "x-api-key": api_key
        }
    )

    device_id = response.json["id"]

    response = client.delete(f"/scim/v2/Devices/{device_id}", headers={
        "x-api-key": api_key
    })

    assert response.status_code == 204

    response = client.get(f"/scim/v2/Devices/{device_id}", headers={
        "x-api-key": api_key
    })

    assert response.status_code == 404

    response = client.get("/scim/v2/Devices", headers={
        "x-api-key": api_key
    })

    assert response.status_code == 200
    print(response.json)
    assert response.json["totalResults"] == 0
    assert response.json["schemas"] == [
        "urn:ietf:params:scim:api:messages:2.0:ListResponse"]
    assert len(response.json["Resources"]) == 0


def test_create_endpoint_app_cert(client: FlaskClient, api_key: str):
    """ Test POST Endpoint Apps """
    response = client.post(
        "/scim/v2/EndpointApps",
        json={
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:EndpointApp"],
            "applicationType": "deviceControl",
            "applicationName": "Device Control App 1",
            "certificateInfo": {
                "rootPublicKey": 
                "MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAxzCip+h22/jEi3O6rExv"
                "GSxrmLjk+pkor7gzsjLcZ2vi1N5KBTSmhDdn7O9wSg16DyP45wjb22p2dczVkR6P"
                "WHFFgEQ0aIojdSFxng7zMybCqinqADP3wposzFRpHxtl346B0SYuMdvjLw8d1Qht"
                "aRm1pwp+0kH3iCQGz/fMPrkOf5NrbWvE241YUrRqowRb32GY3V63FJHcwf2mI/7j"
                "pkQteFonRc8kGt0XLu+Xhn/jdT2U9hFrEaWy5DVrz3uAAmhHmESuiP1jHBJXuvcK"
                "fX66YMSpaJOaS12W4i1QzNnmbHreKile43AcbaxH3bY+4QhBWk3k7RBqQtFGjdu+"
                "DQIDAQAB",
                "subjectName": "www.example.com"
            },
        },
        headers={
            "x-api-key": api_key
        }
    )

    assert response.status_code == 201
    print(response.json)

    assert response.json["id"] is not None
    assert response.json["meta"] is not None
    assert response.json["schemas"] == [
        "urn:ietf:params:scim:schemas:core:2.0:EndpointApp"
    ]
    assert response.json["clientToken"] is None
    assert response.json["certificateInfo"] == {
        "rootPublicKey":
        "MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAxzCip+h22/jEi3O6rExv"
        "GSxrmLjk+pkor7gzsjLcZ2vi1N5KBTSmhDdn7O9wSg16DyP45wjb22p2dczVkR6P"
        "WHFFgEQ0aIojdSFxng7zMybCqinqADP3wposzFRpHxtl346B0SYuMdvjLw8d1Qht"
        "aRm1pwp+0kH3iCQGz/fMPrkOf5NrbWvE241YUrRqowRb32GY3V63FJHcwf2mI/7j"
        "pkQteFonRc8kGt0XLu+Xhn/jdT2U9hFrEaWy5DVrz3uAAmhHmESuiP1jHBJXuvcK"
        "fX66YMSpaJOaS12W4i1QzNnmbHreKile43AcbaxH3bY+4QhBWk3k7RBqQtFGjdu+"
        "DQIDAQAB",
        "subjectName": "www.example.com"
    }


def test_create_endpoint_app_token(client: FlaskClient, api_key: str):
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

    assert response.status_code == 201
    print(response.json)

    assert response.json["id"] is not None
    assert response.json["meta"] is not None
    assert response.json["schemas"] == [
        "urn:ietf:params:scim:schemas:core:2.0:EndpointApp"
    ]
    assert response.json["clientToken"] is not None
