# Copyright (c) 2023, Cisco and/or its affiliates.
# All rights reserved.
# See LICENSE file in this distribution.
# SPDX-License-Identifier: Apache-2.0

""" Test the scim device model """

import json

from uuid import uuid4
from tiedie.models.scim import (
    Application, BleExtension, Device, DppExtension,
    EndpointAppsExtension, PairingJustWorks, PairingPassKey, ZigbeeExtension
)


def test_ble_device_creation():
    """ Test the creation of a device """
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

    device_json = device.model_dump_json(by_alias=True, exclude_none=True)

    expected = json.dumps({
        "deviceDisplayName": "BLE Monitor",
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
    }, separators=(',', ':'))
    assert device_json == expected

    device2 = Device.model_validate_json(device_json)
    assert device == device2

    device = Device(
        device_display_name="BLE Monitor",
        admin_state=False,
        ble_extension=BleExtension(
            device_mac_address="AA:BB:CC:11:22:33",
            is_random=False,
            version_support=["4.1", "4.2", "5.0", "5.1", "5.2", "5.3"],
            pairing_just_works=PairingJustWorks(key=123456)
        )
    )

    expected = json.dumps({
        "deviceDisplayName": "BLE Monitor",
        "adminState": False,
        "urn:ietf:params:scim:schemas:extension:ble:2.0:Device": {
            "versionSupport": [
                "4.1",
                "4.2",
                "5.0",
                "5.1",
                "5.2",
                "5.3"
            ],
            "deviceMacAddress": "AA:BB:CC:11:22:33",
            "isRandom": False,
            "urn:ietf:params:scim:schemas:extension:pairingJustWorks:2.0:Device": {
                "key": 123456
            },
            "pairingMethods": [
                "urn:ietf:params:scim:schemas:extension:pairingJustWorks:2.0:Device"
            ]
        },
        "schemas": [
            "urn:ietf:params:scim:schemas:core:2.0:Device",
            "urn:ietf:params:scim:schemas:extension:ble:2.0:Device"
        ]
    }, separators=(',', ':'))

    device_json = device.model_dump_json(by_alias=True, exclude_none=True)

    assert device_json == expected


def test_zigbee_device_creation():
    """ Test the creation of a zigbee device """
    device = Device(
        device_display_name="Zigbee Monitor",
        admin_state=False,
        zigbee_extension=ZigbeeExtension(
            version_support=["3.0"],
            device_eui64_address="50325FFFFEE76728"
        )
    )

    expected = json.dumps({
        "deviceDisplayName": "Zigbee Monitor",
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
    }, separators=(',', ':'))

    device_json = device.model_dump_json(by_alias=True, exclude_none=True)
    assert device_json == expected

    device2 = Device.model_validate_json(device_json)
    assert device == device2


def test_dpp_device_creation():
    """ Test the creation of a dpp device """
    device = Device(
        device_display_name="DPP Monitor",
        admin_state=False,
        dpp_extension=DppExtension(
            dpp_version=2,
            bootstrapping_method=["QR"],
            bootstrap_key=("MDkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDIg"
                           "ADURzxmttZoIRIPWGoQMV00XHWCAQIhXruVWOz0NjlkIA="),
            device_mac_address="AA:BB:CC:11:22:33",
            class_channel=["81/1", "115/36"],
            serial_number="4774LH2b4044"
        )
    )

    expected = json.dumps({
        "deviceDisplayName": "DPP Monitor",
        "adminState": False,
        "urn:ietf:params:scim:schemas:extension:dpp:2.0:Device": {
            "dppVersion": 2,
            "bootstrappingMethod": [
                "QR"
            ],
            "bootstrapKey":
            "MDkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDIgADURzxmttZoIRIPWGoQMV00XHWCAQIhXruVWOz0NjlkIA=",
            "deviceMacAddress": "AA:BB:CC:11:22:33",
            "classChannel": [
                "81/1",
                "115/36"
            ],
            "serialNumber": "4774LH2b4044"
        },
        "schemas": [
            "urn:ietf:params:scim:schemas:core:2.0:Device",
            "urn:ietf:params:scim:schemas:extension:dpp:2.0:Device"
        ]
    }, separators=(',', ':'))

    device_json = device.model_dump_json(by_alias=True, exclude_none=True)
    assert device_json == expected

    device2 = Device.model_validate_json(device_json)
    assert device == device2


def test_endpoint_extension():
    """ Test the creation of an endpoint extension """

    control_app_id = str(uuid4())
    data_app_id = str(uuid4())

    device = Device(
        device_display_name="BLE Monitor",
        admin_state=False,
        ble_extension=BleExtension(
            device_mac_address="AA:BB:CC:11:22:33",
            is_random=False,
            version_support=["4.1", "4.2", "5.0", "5.1", "5.2", "5.3"],
            pairing_pass_key=PairingPassKey(key=123456)
        ),
        endpoint_apps_extension=EndpointAppsExtension(
            applications=[
                Application(value=control_app_id),
                Application(value=data_app_id)
            ]
        )
    )

    device_json = device.model_dump_json(by_alias=True, exclude_none=True)

    expected = json.dumps({
        "deviceDisplayName": "BLE Monitor",
        "adminState": False,
        "urn:ietf:params:scim:schemas:extension:ble:2.0:Device": {
            "versionSupport": [
                "4.1",
                "4.2",
                "5.0",
                "5.1",
                "5.2",
                "5.3"
            ],
            "deviceMacAddress": "AA:BB:CC:11:22:33",
            "isRandom": False,
            "urn:ietf:params:scim:schemas:extension:pairingPassKey:2.0:Device": {
                "key": 123456
            },
            "pairingMethods": [
                "urn:ietf:params:scim:schemas:extension:pairingPassKey:2.0:Device"
            ]
        },
        "urn:ietf:params:scim:schemas:extension:endpointAppsExt:2.0:Device": {
            "applications": [
                {
                    "value": control_app_id
                },
                {
                    "value": data_app_id
                }
            ]
        },
        "schemas": [
            "urn:ietf:params:scim:schemas:core:2.0:Device",
            "urn:ietf:params:scim:schemas:extension:ble:2.0:Device",
            "urn:ietf:params:scim:schemas:extension:endpointApps:2.0:Device"
        ]
    }, separators=(',', ':'))

    assert device_json == expected

    device2 = Device.model_validate_json(device_json)
    assert device == device2
