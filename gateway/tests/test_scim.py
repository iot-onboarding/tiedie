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
                "rootCA":
                "MIIFhjCCA26gAwIBAgIUHDSTmhKfAyFd6AswCPyJ1OfjhVAwDQYJKoZIhvcNAQEL"
                "BQAwSTEXMBUGA1UEAwwOVGllRGllIFRlc3QgQ0ExCzAJBgNVBAYTAlVTMQ4wDAYD"
                "VQQKDAVNeU9yZzERMA8GA1UECwwIQ0EuNDgxODEwHhcNMjMxMDIzMjIyNzMzWhcN"
                "MjQxMDIyMjIyNzMzWjBJMRcwFQYDVQQDDA5UaWVEaWUgVGVzdCBDQTELMAkGA1UE"
                "BhMCVVMxDjAMBgNVBAoMBU15T3JnMREwDwYDVQQLDAhDQS40ODE4MTCCAiIwDQYJ"
                "KoZIhvcNAQEBBQADggIPADCCAgoCggIBAM9MtDrSIIBU2o3DgrJ8wy7JNTsVoOJM"
                "BTJ1/jg20U5s/txX0qs0Jtx2EQOGQsvLlPaB9LHWPycUIz4rGl3B+kfsly3rQFfV"
                "q2Ff/y8RkXwCF77aauua+yXmFw3ct+bgy2vSjAMzbRXA958HIameWQC0VOLzpCAF"
                "hgKyjLwR/YCpZxX0TOlFpN9DrfhSCUItSNTivPh3bHtdcbr5QRfbnH9OQ3lHKr+g"
                "SNzjrxQSmFQrtqpCtqVdg7O3oOnehHlEm1l8WBgdk0AdGYZ5TpUu/sxdi8h25xrw"
                "Cq8Lytv9zC9yCszTFqHDM8ralulVLizTznvGJNVg6utWmbmd8nMeYh0Ii3oQ9QHB"
                "FSbHR3njD4TR8nR7UXaf02BmTH7BrrSp81ALvjWQWAGqvHT6ORD93Jz2E7pRmfk1"
                "Lmw7Zniglg2ur+zOmRdAJUoEEJKh9G9sdzEm+kPtkBV15mVkBAbaRG2KMBdiiqm/"
                "MAuUaaWvcUrBH65gQBUTabb7fV9/iA13B7DlyYPFN+h/RBpnUSBTv2pr7ugdlbjk"
                "CUwvyCjLrMCMJ5tRqtM4Lj5RKXJ2haUG+am570e7MV8gfwmcYfvO0YjI7qoNAVNI"
                "jim+OLENWUWEHk60Tywo3+SvWllZDCAk1cihzeKggObNiZD72YCOmvO4D5+ebJgo"
                "chdaY7nu+qqLAgMBAAGjZjBkMB0GA1UdDgQWBBQ5WFERwi5JUHOqtITJdzBC0gBj"
                "UjAfBgNVHSMEGDAWgBQ5WFERwi5JUHOqtITJdzBC0gBjUjASBgNVHRMBAf8ECDAG"
                "AQH/AgEAMA4GA1UdDwEB/wQEAwIBBjANBgkqhkiG9w0BAQsFAAOCAgEAysEKRzgP"
                "vgsmyf+ncJLBDxYKJgOa3NHOvdSDL/x9ruPaHk60Qtdam/Irk9XC96Smx+4OC9RY"
                "bx0D06GO40IUKlMssLU3eh4G7LTwNYeNFxMgPrkYsdyKlVqOTZMVdErNmo4zpVwa"
                "T7ZRrGkJvlcjIuIFmGE8JWKZUj+7g7hmM9KPRz4Ie8kCb/W5eVzvnJ2ZhEMh+aMi"
                "9auE+v98YRqkrK3T+IWTCke4QvDHmGxCxml8MKwxFvuqDbnWkGxvGWM1K1xWhaf6"
                "I92HtWKeLOIIC29S3EJoQapBHwOFWIo6rCfZkucTTQ5TfaAOv9LpcspnQKLSJxPN"
                "jvCHUwKitxMBvKjCL7Fne8311G2ydIc4h4Z4WT3XCKVEAvTCRjv2067lKNGMNGfe"
                "LGkBzueAaGiBYQ4Ex2KvlbbtaAzCVxfI+SwjynJJoLriRQKCVEQbaoVl3MoK7ktx"
                "Gl2fZRrN5krJ3F2wbQLuS5Wr8j5+FUNb7k6ivSjYALmDn2K+HCWF1+9FAki98ge6"
                "UPgCcDS92aUTtMsvOQ80LnzYkxK7vYS/tRZGWfuTlZoZjFDNOhIe8zy2bYw1Tm2X"
                "5vDMen6JX3MJ94XsEkco6g8AkjXHisnBqgNGDRYXMIO/uBmQEhMNBpiy9eYJWI2D"
                "B7vpBipQ/6G5kI52j8azwyjkIYgOOFv/Hoo=",
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
        "rootCA":
            "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"
            "B7vpBipQ/6G5kI52j8azwyjkIYgOOFv/Hoo=",
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
