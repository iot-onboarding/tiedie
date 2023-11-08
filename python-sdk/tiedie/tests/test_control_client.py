""" Test Control Client """

import json
from uuid import uuid4
import pytest
import responses
from responses import matchers

from tiedie.api.auth import ApiKeyAuthenticator, CertificateAuthenticator
from tiedie.api.control_client import ControlClient
from tiedie.models.ble import (AdvertisementRegistrationOptions,
                               BleAdvertisementFilter,
                               BleAdvertisementFilterType,
                               BleConnectRequest,
                               BleDataParameter,
                               BleService)
from tiedie.models.common import ConnectionRegistrationOptions, DataRegistrationOptions
from tiedie.models.responses import TiedieStatus
from tiedie.models.scim import BleExtension, Device, PairingPassKey


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


def test_create_binding(mock_server: responses.RequestsMock,
                        control_client: ControlClient):
    """ Test create binding """

    device_id = str(uuid4())

    body = json.dumps({
        "status": "SUCCESS",
    }, separators=(',', ':'))

    mock_server.post(
        "https://control.example.com/nipc/connectivity/binding",
        body=body,
        status=200,
        match=[
            matchers.json_params_matcher({
                "id": device_id,
                "technology": "ble",
            }),
        ],
        content_type="application/json",
    )

    device = Device(
        device_display_name="BLE Monitor",
        admin_state=False,
        device_id=device_id,
        ble_extension=BleExtension(
            device_mac_address="AA:BB:CC:11:22:33",
            is_random=False,
            version_support=["4.1", "4.2", "5.0", "5.1", "5.2", "5.3"],
            pairing_pass_key=PairingPassKey(key=123456)
        )
    )

    response = control_client.create_binding(device)

    assert response.http.status_code == 200
    assert response.status == TiedieStatus.SUCCESS
    assert response.body is None


def test_connect(mock_server: responses.RequestsMock,
                 control_client: ControlClient):
    """ Test connect """

    device_id = str(uuid4())

    body = json.dumps({
        "status": "SUCCESS",
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
    }, separators=(',', ':'))

    mock_server.post(
        "https://control.example.com/nipc/connectivity/connection",
        body=body,
        status=200,
        match=[
            matchers.json_params_matcher({
                "id": device_id,
                "technology": "ble",
                "ble": {
                    "retries": 3,
                    "retryMultipleAPs": True,
                }
            }),
        ],
        content_type="application/json",
    )
    mock_server.post(
        "https://control.example.com/nipc/connectivity/connection",
        body=body,
        status=200,
        match=[
            matchers.json_params_matcher({
                "id": device_id,
                "technology": "ble",
                "ble": {
                    "services": [
                        {
                            "serviceID": "1800"
                        },
                        {
                            "serviceID": "1801"
                        }
                    ],
                    "retries": 5,
                    "retryMultipleAPs": False,
                }
            })
        ],
        content_type="application/json",
    )

    device = Device(
        device_display_name="BLE Monitor",
        admin_state=False,
        device_id=device_id,
        ble_extension=BleExtension(
            device_mac_address="AA:BB:CC:11:22:33",
            is_random=False,
            version_support=["4.1", "4.2", "5.0", "5.1", "5.2", "5.3"],
            pairing_pass_key=PairingPassKey(key=123456)
        )
    )

    response = control_client.connect(device)

    assert response.http.status_code == 200
    assert response.status == TiedieStatus.SUCCESS
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

    response = control_client.connect(device,
                                      BleConnectRequest(retries=5,
                                                        services=[
                                                            BleService(
                                                                service_id="1800"),
                                                            BleService(
                                                                service_id="1801")],
                                                        retry_multiple_aps=False))

    assert response.http.status_code == 200
    assert response.status == TiedieStatus.SUCCESS
    assert response.body is not None
    assert isinstance(response.body[0], BleDataParameter)
    assert response.body[0].service_id == "1800"
    assert response.body[0].characteristic_id == "2a00"
    assert response.body[0].flags == ["read", "write"]


def test_disconnect(mock_server: responses.RequestsMock,
                    control_client: ControlClient):
    """ Test disconnect """

    device_id = str(uuid4())

    body = json.dumps({
        "status": "SUCCESS",
    }, separators=(',', ':'))

    mock_server.delete(
        "https://control.example.com/nipc/connectivity/connection",
        body=body,
        status=200,
        match=[matchers.query_param_matcher({"id": device_id})],
        content_type="application/json",
    )

    device = Device(
        device_display_name="BLE Monitor",
        admin_state=False,
        device_id=device_id,
        ble_extension=BleExtension(
            device_mac_address="AA:BB:CC:11:22:33",
            is_random=False,
            version_support=["4.1", "4.2", "5.0", "5.1", "5.2", "5.3"],
            pairing_pass_key=PairingPassKey(key=123456)
        )
    )

    response = control_client.disconnect(device)

    assert response.http.status_code == 200
    assert response.status == TiedieStatus.SUCCESS
    assert response.body is None


def test_discovery(mock_server: responses.RequestsMock,
                   control_client: ControlClient):
    """ Test Discovery """

    device_id = str(uuid4())

    body = json.dumps({
        "status": "SUCCESS",
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
    }, separators=(',', ':'))

    mock_server.get(
        "https://control.example.com/nipc/connectivity/services",
        body=body,
        status=200,
        match=[
            matchers.query_param_matcher({
                "id": device_id,
                "technology": "ble",
                "ble[retries]": 3,
                "ble[retryMultipleAPs]": True
            }),
        ],
        content_type="application/json",
    )
    mock_server.get(
        "https://control.example.com/nipc/connectivity/services",
        body=body,
        status=200,
        match=[
            matchers.query_param_matcher({
                "id": device_id,
                "technology": "ble",
                "ble[services][serviceID]": ["1800", "1801"],
                "ble[retries]": 5,
                "ble[retryMultipleAPs]": False
            })
        ],
        content_type="application/json",
    )

    device = Device(
        device_display_name="BLE Monitor",
        admin_state=False,
        device_id=device_id,
        ble_extension=BleExtension(
            device_mac_address="AA:BB:CC:11:22:33",
            is_random=False,
            version_support=["4.1", "4.2", "5.0", "5.1", "5.2", "5.3"],
            pairing_pass_key=PairingPassKey(key=123456)
        )
    )

    response = control_client.discover(device)

    assert response.http.status_code == 200
    assert response.status == TiedieStatus.SUCCESS
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

    response = control_client.discover(device,
                                       BleConnectRequest(retries=5,
                                                         services=[
                                                             BleService(
                                                                 service_id="1800"),
                                                             BleService(
                                                                 service_id="1801")],
                                                         retry_multiple_aps=False))

    assert response.http.status_code == 200
    assert response.status == TiedieStatus.SUCCESS
    assert response.body is not None
    assert isinstance(response.body[0], BleDataParameter)
    assert response.body[0].service_id == "1800"
    assert response.body[0].characteristic_id == "2a00"
    assert response.body[0].flags == ["read", "write"]


def test_read(mock_server: responses.RequestsMock,
              control_client: ControlClient):
    """ Test read """

    device_id = str(uuid4())

    body = json.dumps({
        "status": "SUCCESS",
        "value": "00001111"
    }, separators=(',', ':'))

    mock_server.get(
        "https://control.example.com/nipc/data/attribute",
        body=body,
        status=200,
        match=[
            matchers.query_param_matcher({
                "id": device_id,
                "technology": "ble",
                "ble[serviceID]": "1800",
                "ble[characteristicID]": "2a00",
            }),
        ],
        content_type="application/json",
    )

    device = Device(
        device_display_name="BLE Monitor",
        admin_state=False,
        device_id=device_id,
        ble_extension=BleExtension(
            device_mac_address="AA:BB:CC:11:22:33",
            is_random=False,
            version_support=["4.1", "4.2", "5.0", "5.1", "5.2", "5.3"],
            pairing_pass_key=PairingPassKey(key=123456)
        )
    )

    response = control_client.read(device, BleDataParameter(
        device_id=device_id,
        service_id="1800",
        characteristic_id="2a00"
    ))

    assert response.http.status_code == 200
    assert response.status == TiedieStatus.SUCCESS
    assert response.value == "00001111"


def test_write(mock_server: responses.RequestsMock,
               control_client: ControlClient):
    """ Test write """

    device_id = str(uuid4())

    body = json.dumps({
        "status": "SUCCESS",
        "value": "00001111"
    }, separators=(',', ':'))

    mock_server.post(
        "https://control.example.com/nipc/data/attribute",
        body=body,
        status=200,
        match=[
            matchers.json_params_matcher({
                "id": device_id,
                "technology": "ble",
                "value": "00001111",
                "ble": {
                    "serviceID": "1800",
                    "characteristicID": "2a00"
                },
                "zigbee": None
            }),
        ],
        content_type="application/json",
    )

    device = Device(
        device_display_name="BLE Monitor",
        admin_state=False,
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
        BleDataParameter(
            device_id=device_id,
            service_id="1800",
            characteristic_id="2a00"
        ),
        "00001111")

    assert response.http.status_code == 200
    assert response.status == TiedieStatus.SUCCESS
    assert response.value == "00001111"


def test_subscribe(mock_server: responses.RequestsMock,
                   control_client: ControlClient):
    """ Test subscribe """

    device_id = str(uuid4())

    body = json.dumps({
        "status": "SUCCESS"
    }, separators=(',', ':'))

    mock_server.post(
        "https://control.example.com/nipc/data/subscription",
        body=body,
        status=200,
        match=[
            matchers.json_params_matcher({
                "id": device_id,
                "technology": "ble",
                "ble": {
                    "serviceID": "1800",
                    "characteristicID": "2a00"
                },
                "zigbee": None
            }),
        ],
        content_type="application/json",
    )

    device = Device(
        device_display_name="BLE Monitor",
        admin_state=False,
        device_id=device_id,
        ble_extension=BleExtension(
            device_mac_address="AA:BB:CC:11:22:33",
            is_random=False,
            version_support=["4.1", "4.2", "5.0", "5.1", "5.2", "5.3"],
            pairing_pass_key=PairingPassKey(key=123456)
        )
    )

    response = control_client.subscribe(
        device,
        BleDataParameter(
            device_id=device_id,
            service_id="1800",
            characteristic_id="2a00"
        ))

    assert response.http.status_code == 200
    assert response.status == TiedieStatus.SUCCESS
    assert response.body is None


def test_unsubscribe(mock_server: responses.RequestsMock,
                     control_client: ControlClient):
    """ Test unsubscribe """

    device_id = str(uuid4())

    body = json.dumps({
        "status": "SUCCESS"
    }, separators=(',', ':'))

    mock_server.delete(
        "https://control.example.com/nipc/data/subscription",
        body=body,
        status=200,
        match=[
            matchers.query_param_matcher({
                "id": device_id,
                "technology": "ble",
                "ble[serviceID]": "1800",
                "ble[characteristicID]": "2a00",
            }),
        ],
        content_type="application/json",
    )

    device = Device(
        device_display_name="BLE Monitor",
        admin_state=False,
        device_id=device_id,
        ble_extension=BleExtension(
            device_mac_address="AA:BB:CC:11:22:33",
            is_random=False,
            version_support=["4.1", "4.2", "5.0", "5.1", "5.2", "5.3"],
            pairing_pass_key=PairingPassKey(key=123456)
        )
    )

    response = control_client.unsubscribe(
        device,
        BleDataParameter(
            device_id=device_id,
            service_id="1800",
            characteristic_id="2a00"
        ))

    assert response.http.status_code == 200
    assert response.status == TiedieStatus.SUCCESS
    assert response.body is None


def test_register_topic(mock_server: responses.RequestsMock,
                        control_client: ControlClient):
    """ Test register topic """

    topic = "enterprise/hospital/pulse_oximeter"
    device_id = str(uuid4())

    body = json.dumps({
        "status": "SUCCESS"
    }, separators=(',', ':'))

    mock_server.post(
        "https://control.example.com/nipc/registration/topic",
        body=body,
        status=200,
        match=[
            matchers.json_params_matcher({
                "technology": "ble",
                "id": device_id,
                "topic": topic,
                "dataFormat": "default",
                "dataApps": [
                    {
                        "dataAppID": "app1"
                    },
                    {
                        "dataAppID": "app2"
                    }
                ],
                "ble": {
                    "type": "gatt",
                    "serviceID": "1800",
                    "characteristicID": "2a00"
                },
                "zigbee": None
            })
        ],
        content_type="application/json",
    )
    mock_server.post(
        "https://control.example.com/nipc/registration/topic",
        body=body,
        status=200,
        match=[
            matchers.json_params_matcher({
                "technology": "ble",
                "id": device_id,
                "topic": topic,
                "dataFormat": "default",
                "dataApps": [{
                    "dataAppID": "app1"
                }, {
                    "dataAppID": "app2"
                }],
                "ble": {
                    "type": "advertisements"
                },
                "zigbee": None
            }),
        ],
        content_type="application/json",
    )
    mock_server.post(
        "https://control.example.com/nipc/registration/topic",
        body=body,
        status=200,
        match=[
            matchers.json_params_matcher({
                "technology": "ble",
                "topic": topic,
                "id": None,
                "dataFormat": "default",
                "dataApps": [{
                    "dataAppID": "app1"
                }, {
                    "dataAppID": "app2"
                }],
                "ble": {
                    "type": "advertisements",
                    "filterType": "allow",
                    "filters": [{
                        "mac": "1800",
                        "adType": "2a00",
                        "adData": "0001"
                    }, {
                        "mac": "1800",
                        "adType": "2a01",
                        "adData": "0002"
                    }]
                },
                "zigbee": None
            }),
        ],
        content_type="application/json",
    )
    mock_server.post(
        "https://control.example.com/nipc/registration/topic",
        body=body,
        status=200,
        match=[
            matchers.json_params_matcher({
                "technology": "ble",
                "id": device_id,
                "topic": topic,
                "dataFormat": "default",
                "dataApps": [{
                    "dataAppID": "app1"
                }, {
                    "dataAppID": "app2"
                }],
                "ble": {
                    "type": "connection_events"
                },
                "zigbee": None
            }),
        ],
        content_type="application/json",
    )

    device = Device(
        device_display_name="BLE Monitor",
        admin_state=False,
        device_id=device_id,
        ble_extension=BleExtension(
            device_mac_address="AA:BB:CC:11:22:33",
            is_random=False,
            version_support=["4.1", "4.2", "5.0", "5.1", "5.2", "5.3"],
            pairing_pass_key=PairingPassKey(key=123456)
        )
    )

    response = control_client.register_topic(topic, device, DataRegistrationOptions(
        data_apps=["app1", "app2"],
        data_parameter=BleDataParameter(
            device_id=device_id, service_id="1800", characteristic_id="2a00")
    ))

    assert response.http.status_code == 200
    assert response.status == TiedieStatus.SUCCESS

    response = control_client.register_topic(
        topic, device, AdvertisementRegistrationOptions(
            data_apps=["app1", "app2"]
        ))

    assert response.http.status_code == 200
    assert response.status == TiedieStatus.SUCCESS

    response = control_client.register_topic(topic, None, AdvertisementRegistrationOptions(
        data_apps=["app1", "app2"],
        advertisement_filter_type=BleAdvertisementFilterType.ALLOW,
        advertisement_filter=[
            BleAdvertisementFilter(mac="1800", ad_type="2a00", ad_data="0001"),
            BleAdvertisementFilter(mac="1800", ad_type="2a01", ad_data="0002")
        ]
    ))

    assert response.http.status_code == 200
    assert response.status == TiedieStatus.SUCCESS

    response = control_client.register_topic(topic, device, ConnectionRegistrationOptions(
        data_apps=["app1", "app2"],
    ))

    assert response.http.status_code == 200
    assert response.status == TiedieStatus.SUCCESS


def test_unregister_topic(mock_server: responses.RequestsMock,
                          control_client: ControlClient):
    """ Test unregister topic """

    topic = "enterprise/hospital/pulse_oximeter"

    body = json.dumps({
        "status": "SUCCESS"
    }, separators=(',', ':'))

    mock_server.delete(
        "https://control.example.com/nipc/registration/topic",
        body=body,
        status=200,
        match=[
            matchers.query_param_matcher({
                "topic": topic,
            }),
        ],
        content_type="application/json",
    )

    response = control_client.unregister_topic(topic)

    assert response.http.status_code == 200
    assert response.status == TiedieStatus.SUCCESS
    assert response.body is None
