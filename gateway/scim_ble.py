# Copyright (c) 2023, Cisco Systems, Inc. and/or its affiliates.
# All rights reserved.
# See LICENSE file in this distribution.
# SPDX-License-Identifier: Apache-2.0

"""
This module implements BLE dispatch for SCIM.
"""

from tiedie_exceptions import DeviceExists
from models import BleExtension
from database import session

def ble_create_device(request,device_id):
    """
    Process BLE SCIM creation request.  Return a BleExtension()
    """
    ble_json = request.json.get("urn:ietf:params:scim:schemas:extension:ble:2.0:Device")
    device_mac_address = ble_json.get("deviceMacAddress")

    pairing_just_works = ble_json.get(
        "urn:ietf:params:scim:schemas:extension:pairingJustWorks:2.0:Device")
    pairing_just_works_key = None
    pairing_pass_key = None
    pairing_oob_key = None
    pairing_oobrn = None

    if pairing_just_works:
        pairing_just_works_key = pairing_just_works.get("key")
    pairing_pass = ble_json.get(
        "urn:ietf:params:scim:schemas:extension:pairingPassKey:2.0:Device")
    if pairing_pass:
        pairing_pass_key = pairing_pass.get("key")
    pairing = ble_json.get(
        "urn:ietf:params:scim:schemas:extension:pairingOOB:2.0:Device")
    if pairing:
        pairing_oob_key = pairing.get("key")
        pairing_oobrn = pairing.get("randNumber")

    existing_device = BleExtension.query.filter_by(
        device_mac_address=device_mac_address).first()

    if existing_device:
        raise DeviceExists("Device Exists")

    entry = BleExtension(
        device_id=device_id,
        version_support = ble_json.get("versionSupport"),
        device_mac_address=device_mac_address,
        is_random=ble_json.get("isRandom"),
        separate_broadcast_address = ble_json.get("separateBroadcastAddress", []),
        irk = ble_json.get("irk", ""),
        pairing_methods = ble_json.get("pairingMethods", []),
        pairing_null = ble_json.get(
                "urn:ietf:params:scim:schemas:extension:pairingNull:2.0:Device"),
        pairing_just_works_keys=pairing_just_works_key,
        pairing_pass_key=pairing_pass_key,
        pairing_oob_key=pairing_oob_key,
        pairing_oobrn=pairing_oobrn,
    )
    return entry



def ble_update_device(request):
    """
    Update SCIM entry for BLE device.
    """
    entry: BleExtension = session.get(BleExtension,request.json["id"])
    # if ble is added in update, just add it.
    if not entry:
        return ble_create_device(request,request.json["id"])


    ble_json=request.json["urn:ietf:params:scim:schemas:extension:ble:2.0:Device"]
    entry.version_support = ble_json.get("versionSupport")
    entry.device_mac_address = ble_json.get("deviceMacAddress")
    entry.is_random = ble_json.get("isRandom")
    entry.pairing_methods = ble_json.get("pairingMethods")
    entry.pairing_null = ble_json.get(
        "urn:ietf:params:scim:schemas:extension:pairingNull:2.0:Device")
    entry.pairing_just_works_key = ble_json.get(
        "urn:ietf:params:scim:schemas:extension:pairingJustWorks:2.0:Device").get("key")
    entry.pairing_pass_key = ble_json.get(
        "urn:ietf:params:scim:schemas:extension:pairingPassKey:2.0:Device").get("key")
    entry.pairing_oob_key = ble_json.get(
        "urn:ietf:params:scim:schemas:extension:pairingOOB:2.0:Device").get("key")
    entry.pairing_oobrn = ble_json.get(
        "urn:ietf:params:scim:schemas:extension:pairingOOB:2.0:Device").get("randNumber")

    return entry

def ble_get_filtered_entries(mac_address):
    """ returned filtered list """

    return BleExtension.query.filter_by(device_mac_address=mac_address).all()
