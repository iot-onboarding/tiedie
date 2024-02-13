# Copyright (c) 2023, Cisco Systems, Inc. and/or its affiliates.
# All rights reserved.
# See LICENSE file in this distribution.
# SPDX-License-Identifier: Apache-2.0

"""
This module implements BLE dispatch for SCIM.
"""

from flask import jsonify, make_response
from sqlalchemy import select
from models import EndpointApp, BleDevice
from database import session
from scim_error import blow_an_error

def ble_create_device(request,core):
    """
    Process BLE SCIM creation request.  Returns SCIM object or error.
    """
    device_mac_address = request.json["urn:ietf:params:scim:schemas:extension:ble:2.0:Device"].get(
        "deviceMacAddress")

    pairing_just_works = request.json["urn:ietf:params:scim:schemas:extension:ble:2.0:Device"].get(
        "urn:ietf:params:scim:schemas:extension:pairingJustWorks:2.0:Device")
    pairing_just_works_key = None
    pairing_pass_key = None
    pairing_oob_key = None
    pairing_oobrn = None

    endpoint_apps = None
    endpoint_apps_ext = request.json.get(
        "urn:ietf:params:scim:schemas:extension:endpointAppsExt:2.0:Device", None)
    if endpoint_apps_ext is not None:
        applications = endpoint_apps_ext.get("applications")
        endpoint_app_ids = [app.get("value") for app in applications]
        # Select all endpoint apps from the database
        endpoint_apps = session.scalars(select(EndpointApp).filter(
            EndpointApp.id.in_(endpoint_app_ids))).all()

    if pairing_just_works:
        pairing_just_works_key = pairing_just_works.get("key")
    pairing_pass = request.json["urn:ietf:params:scim:schemas:extension:ble:2.0:Device"].get(
        "urn:ietf:params:scim:schemas:extension:pairingPassKey:2.0:Device")
    if pairing_pass:
        pairing_pass_key = pairing_pass.get("key")
    pairing = request.json["urn:ietf:params:scim:schemas:extension:ble:2.0:Device"].get(
        "urn:ietf:params:scim:schemas:extension:pairingOOB:2.0:Device")
    if pairing:
        pairing_oob_key = pairing.get("key")
        pairing_oobrn = pairing.get("randNumber")
    device_id = request.json.get("id")

    existing_device = BleDevice.query.filter_by(
        device_mac_address=device_mac_address).first()

    if existing_device:
        return blow_an_error("Device already exists in the database.",409)

    try:
        entry = BleDevice(
            device_id=device_id,
            version_support = request.json[
                "urn:ietf:params:scim:schemas:extension:ble:2.0:Device"].get(
                    "versionSupport"),
            device_mac_address=device_mac_address,
            is_random=request.json[
                "urn:ietf:params:scim:schemas:extension:ble:2.0:Device"].get(
                    "isRandom"),
            separate_broadcast_address = request.json[
                "urn:ietf:params:scim:schemas:extension:ble:2.0:Device"].get(
                    "separateBroadcastAddress", []),
            irk = request.json[
                "urn:ietf:params:scim:schemas:extension:ble:2.0:Device"].get(
                    "irk", ""),
            pairing_methods = request.json[
                "urn:ietf:params:scim:schemas:extension:ble:2.0:Device"].get(
                    "pairingMethods", []),
            pairing_null = request.json[
                "urn:ietf:params:scim:schemas:extension:ble:2.0:Device"].get(
                    "urn:ietf:params:scim:schemas:extension:pairingNull:2.0:Device"),
            pairing_just_works_keys=pairing_just_works_key,
            pairing_pass_key=pairing_pass_key,
            pairing_oob_key=pairing_oob_key,
            pairing_oobrn=pairing_oobrn,
            endpoint_apps=endpoint_apps
        )
        session.add(entry)

        session.commit()
        return entry.serialize(core)
    except Exception as e:
        return blow_an_error(str(e),400)

def ble_update_device(request,core):
    """
    Update SCIM entry for BLE device.
    """
    entry: BleDevice = session.get(BleDevice,request.json["id"])
    # if ble is added in update, just add it.
    if not entry:
        return ble_create_device(request,core)

    entry.version_support = request.json[
        "urn:ietf:params:scim:schemas:extension:ble:2.0:Device"].get(
        "versionSupport")
    entry.device_mac_address = request.json[
        "urn:ietf:params:scim:schemas:extension:ble:2.0:Device"].get(
        "deviceMacAddress")
    entry.is_random = request.json["urn:ietf:params:scim:schemas:extension:ble:2.0:Device"].get(
        "isRandom")
    entry.pairing_methods = request.json[
        "urn:ietf:params:scim:schemas:extension:ble:2.0:Device"].get(
        "urn:ietf:params:scim:schemas:extension:pairingNull:2.0:Device")
    entry.pairing_null = request.json[
        "urn:ietf:params:scim:schemas:extension:ble:2.0:Device"].get(
        "urn:ietf:params:scim:schemas:extension:pairingNull:2.0:Device")
    entry.pairing_just_works_key = request.json[
        "urn:ietf:params:scim:schemas:extension:ble:2.0:Device"][
        "urn:ietf:params:scim:schemas:extension:pairingJustWorks:2.0:Device"].get("key")
    entry.pairing_pass_key = request.json["urn:ietf:params:scim:schemas:extension:ble:2.0:Device"][
        "urn:ietf:params:scim:schemas:extension:pairingPassKey:2.0:Device"].get("key")
    entry.pairing_oob_key = request.json["urn:ietf:params:scim:schemas:extension:ble:2.0:Device"][
        "urn:ietf:params:scim:schemas:extension:pairingOOB:2.0:Device"].get("key")
    entry.pairing_oobrn = request.json["urn:ietf:params:scim:schemas:extension:ble:2.0:Device"][
        "urn:ietf:params:scim:schemas:extension:pairingOOB:2.0:Device"].get("randNumber")

    session.commit()
    return make_response(jsonify(entry.serialize()), 200)
