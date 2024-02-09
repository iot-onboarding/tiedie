# Copyright (c) 2023, Cisco Systems, Inc. and/or its affiliates.
# All rights reserved.
# See LICENSE file in this distribution.
# SPDX-License-Identifier: Apache-2.0

"""
This module implements BLE dispatch for SCIM.
"""

import datetime
from flask import jsonify, make_response
from sqlalchemy import select
from models import EndpointApp, BleDevice
from database import session


def ble_create_device(request):
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

    existing_device = Device.query.filter_by(
        device_mac_address=device_mac_address).first()

    if existing_device:
        return make_response(
            jsonify(
                {
                    "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Device"],
                    "detail": "User already exists in the database.",
                    "status": 409,
                }
            ),
            409,
        )

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
            endpoint_apps=endpoint_apps,
            created_time=datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
        )
        session.add(entry)

        session.commit()
        return make_response(jsonify(entry.serialize()), 201)
    except Exception as e:
        return make_response(
            jsonify(
                {
                    "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Error"],
                    "scimType": "invalidSyntax",
                    "detail": str(e),
                    "status": 400,
                }
            ),
            400,
        )

def ble_update_device(request,user):
    """
    Update SCIM entry for BLE device.
    """

    user.id = request.json.get("id")
    user.device_display_name = request.json.get("deviceDisplayName")
    user.admin_state = request.json.get("adminState")
    user.version_support = request.json[
        "urn:ietf:params:scim:schemas:extension:ble:2.0:Device"].get(
        "versionSupport")
    user.device_mac_address = request.json[
        "urn:ietf:params:scim:schemas:extension:ble:2.0:Device"].get(
        "deviceMacAddress")
    user.is_random = request.json["urn:ietf:params:scim:schemas:extension:ble:2.0:Device"].get(
        "isRandom")
    user.pairing_methods = request.json[
        "urn:ietf:params:scim:schemas:extension:ble:2.0:Device"].get(
        "urn:ietf:params:scim:schemas:extension:pairingNull:2.0:Device")
    user.pairing_null = request.json[
        "urn:ietf:params:scim:schemas:extension:ble:2.0:Device"].get(
        "urn:ietf:params:scim:schemas:extension:pairingNull:2.0:Device")
    user.pairing_just_works_key = request.json[
        "urn:ietf:params:scim:schemas:extension:ble:2.0:Device"][
        "urn:ietf:params:scim:schemas:extension:pairingJustWorks:2.0:Device"].get("key")
    user.pairing_pass_key = request.json["urn:ietf:params:scim:schemas:extension:ble:2.0:Device"][
        "urn:ietf:params:scim:schemas:extension:pairingPassKey:2.0:Device"].get("key")
    user.pairing_oob_key = request.json["urn:ietf:params:scim:schemas:extension:ble:2.0:Device"][
        "urn:ietf:params:scim:schemas:extension:pairingOOB:2.0:Device"].get("key")
    user.pairing_oobrn = request.json["urn:ietf:params:scim:schemas:extension:ble:2.0:Device"][
        "urn:ietf:params:scim:schemas:extension:pairingOOB:2.0:Device"].get("randNumber")
    user.modified_time = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")

    session.commit()
    return make_response(jsonify(user.serialize()), 200)
