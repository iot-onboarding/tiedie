# Copyright (c) 2023, Cisco and/or its affiliates.
# All rights reserved.
# See LICENSE file in this distribution.
# SPDX-License-Identifier: Apache-2.0

"""

This module defines a Flask-based SCIM API with user and endpoint 
app management, authentication, and error handling.

"""

import uuid
import datetime
from functools import wraps
from flask import Blueprint, abort, jsonify, make_response, request, current_app
from sqlalchemy import select
from werkzeug.test import EnvironBuilder
from database import db, session
from models import EndpointApp, User, OnboardingAppKey

from util import make_hash

scim_app = Blueprint("scim", __name__, url_prefix="/scim/v2")

def authenticate_user(func):
    """Verify x-api-key"""

    @wraps(func)
    def check_apikey(*args, **kwargs):
        client_cert = request.environ['peercert']
        if client_cert:
            return func(*args, **kwargs)

        api_key = request.headers.get("X-Api-Key")
        if api_key and bool(OnboardingAppKey.query.filter_by(keyVal=api_key).first()):
            return func(*args, **kwargs)
            return make_response(jsonify({"error": "Unauthorized"}), 403)

    return check_apikey

# SCIM Implementation


@scim_app.route('/Devices', methods=['POST'])
@authenticate_user
def scim_addusers():
    """
    This code defines a SCIM API endpoint for creating users, 
    extracts data from the request JSON, and stores user information in a database.
    """
    # Get the request json and check if it is valid
    if not request.json:
        return make_response(
            jsonify(
                {
                    "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Error"],
                    "scimType": "invalidSyntax",
                    "detail": "Request body is not valid JSON.",
                    "status": 400,
                }
            ),
            400,
        )

    schemas = request.json.get("schemas")
    deviceDisplayName = request.json.get("deviceDisplayName")
    adminState = request.json.get("adminState")
    versionSupport = request.json["urn:ietf:params:scim:schemas:extension:ble:2.0:Device"].get(
        "versionSupport")
    deviceMacAddress = request.json["urn:ietf:params:scim:schemas:extension:ble:2.0:Device"].get(
        "deviceMacAddress")
    isRandom = request.json["urn:ietf:params:scim:schemas:extension:ble:2.0:Device"].get(
        "isRandom")
    separateBroadcastAddress = request.json[
        "urn:ietf:params:scim:schemas:extension:ble:2.0:Device"].get(
        "separateBroadcastAddress", [])
    irk = request.json["urn:ietf:params:scim:schemas:extension:ble:2.0:Device"].get(
        "irk", "")
    pairingMethods = request.json["urn:ietf:params:scim:schemas:extension:ble:2.0:Device"].get(
        "pairingMethods", [])
    pairingNull = request.json["urn:ietf:params:scim:schemas:extension:ble:2.0:Device"].get(
        "urn:ietf:params:scim:schemas:extension:pairingNull:2.0:Device")
    pairingJustWorks = request.json["urn:ietf:params:scim:schemas:extension:ble:2.0:Device"].get(
        "urn:ietf:params:scim:schemas:extension:pairingJustWorks:2.0:Device")
    pairingJustWorksKeys = None
    pairingPassKey = None
    pairingOOBKey = None
    pairingOOBRN = None
    endpoint_apps = None
    endpointAppsExt = request.json.get(
        "urn:ietf:params:scim:schemas:extension:endpointAppsExt:2.0:Device", None)
    if endpointAppsExt is not None:
        applications = endpointAppsExt.get("applications")
        endpoint_app_ids = [app.get("value") for app in applications]
        # Select all endpoint apps from the database
        endpoint_apps = session.scalars(select(EndpointApp).filter(
            EndpointApp.id.in_(endpoint_app_ids))).all()

    if pairingJustWorks:
        pairingJustWorksKeys = pairingJustWorks.get("key")
    pairingPass = request.json["urn:ietf:params:scim:schemas:extension:ble:2.0:Device"].get(
        "urn:ietf:params:scim:schemas:extension:pairingPassKey:2.0:Device")
    if pairingPass:
        pairingPassKey = pairingPass.get("key")
    pairing = request.json["urn:ietf:params:scim:schemas:extension:ble:2.0:Device"].get(
        "urn:ietf:params:scim:schemas:extension:pairingOOB:2.0:Device")
    if pairing:
        pairingOOBKey = pairing.get("key")
        pairingOOBRN = pairing.get("randNumber")

    existing_device = User.query.filter_by(
        deviceMacAddress=deviceMacAddress).first()

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
        user = User(
            schemas=schemas,
            deviceDisplayName=deviceDisplayName,
            adminState=adminState,
            versionSupport=versionSupport,
            deviceMacAddress=deviceMacAddress,
            isRandom=isRandom,
            separateBroadcastAddress=separateBroadcastAddress,
            irk=irk,
            pairingMethods=pairingMethods,
            pairingNull=pairingNull,
            pairingJustWorksKeys=pairingJustWorksKeys,
            pairingPassKey=pairingPassKey,
            pairingOOBKey=pairingOOBKey,
            pairingOOBRN=pairingOOBRN,
            endpointApps=endpoint_apps,
            tCreated=datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
        )
        session.add(user)

        session.commit()
        return make_response(jsonify(user.serialize()), 201)
    except Exception as e:
        return str(e)




@scim_app.route("/Devices/<string:user_id>", methods=["GET"])
@authenticate_user
def get_user(user_id):
    """ 
    SCIM API: Retrieve user data by ID and onboardApp parameters. 
    If not found, a "User not found" response with a status code of 404 is returned.
    """
    onboarding_app = request.args["onboardApp"]
    print(onboarding_app)
    user = User.query.filter_by(id=user_id).join(User.endpointApps).filter_by(applicationName=onboarding_app).first()
    if not user:
        return make_response(
            jsonify(
                {
                    "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Device"],
                    "detail": "User not found",
                    "status": 404,
                }
            ),
            404,
        )
    return jsonify(user.serialize())




@scim_app.route("/Devices/<string:user_id>", methods=["PUT"])
@authenticate_user
def update_user(user_id):
    """
    Function to retrieve SCIM device data based on parameters like start index, count, and filters. 
    It returns a JSON response with a list of serialized devices.
    """
    if not request.json:
        return make_response(
            jsonify(
                {
                    "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Error"],
                    "scimType": "invalidSyntax",
                    "detail": "Request body is not valid JSON.",
                    "status": 400,
                }
            ),
            400,
        )

    onboarding_app = request.args["onboardApp"]
    user = User.query.filter_by(id=user_id).join(User.endpointApps).filter_by(applicationName=onboarding_app).first()

    if not user:
        return make_response(
            jsonify(
                {
                    "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Device",],
                    "detail": "User not found",
                    "status": 404,
                }
            ),
            404,
        )
    else:
        user.id = request.json.get("id")
        user.deviceDisplayName = request.json.get("deviceDisplayName")
        user.adminState = request.json.get("adminState")
        user.versionSupport = request.json[
            "urn:ietf:params:scim:schemas:extension:ble:2.0:Device"].get(
            "versionSupport")
        user.deviceMacAddress = request.json[
            "urn:ietf:params:scim:schemas:extension:ble:2.0:Device"].get(
            "deviceMacAddress")
        user.isRandom = request.json["urn:ietf:params:scim:schemas:extension:ble:2.0:Device"].get(
            "isRandom")
        user.pairingMethods = request.json[
            "urn:ietf:params:scim:schemas:extension:ble:2.0:Device"].get(
            "urn:ietf:params:scim:schemas:extension:pairingNull:2.0:Device")
        user.pairingNull = request.json[
            "urn:ietf:params:scim:schemas:extension:ble:2.0:Device"].get(
            "urn:ietf:params:scim:schemas:extension:pairingNull:2.0:Device")
        user.pairingJustWorksKeys = request.json[
            "urn:ietf:params:scim:schemas:extension:ble:2.0:Device"][
            "urn:ietf:params:scim:schemas:extension:pairingJustWorks:2.0:Device"].get("key")
        user.pairingPassKey = request.json["urn:ietf:params:scim:schemas:extension:ble:2.0:Device"][
            "urn:ietf:params:scim:schemas:extension:pairingPassKey:2.0:Device"].get("key")
        user.pairingOOBKey = request.json["urn:ietf:params:scim:schemas:extension:ble:2.0:Device"][
            "urn:ietf:params:scim:schemas:extension:pairingOOB:2.0:Device"].get("key")
        user.pairingOOBRN = request.json["urn:ietf:params:scim:schemas:extension:ble:2.0:Device"][
            "urn:ietf:params:scim:schemas:extension:pairingOOB:2.0:Device"].get("randNumber")
        user.modTime = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")

        session.commit()
        return make_response(jsonify(user.serialize()), 200)
    

@scim_app.route("/Devices/<string:user_id>", methods=["DELETE"])
@authenticate_user
def delete_user(user_id):
    """Delete SCIM User"""
    onboarding_app = request.args["onboardApp"]
    user = User.query.filter_by(id=user_id).join(User.endpointApps).filter_by(applicationName=onboarding_app).first()
    if not user:
        return make_response(
            jsonify(
                {
                    "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Device"],
                    "detail": "User not found",
                    "status": 404,
                }
            ),
            404,
        )
    else:
        session.delete(user)
        session.commit()
        return make_response("", 204)


@scim_app.route("/Bulk", methods=["POST"])
@authenticate_user
def bulk_command():
    """ Processes SCIM bulk requests, handles operations, and returns summarized results. """
    if request.json is None:
        return make_response(
            jsonify(
                {
                    "schemas": ["urn:ietf:params:scim:api:messages:2.0:Error"],
                    "scimType": "invalidSyntax",
                    "detail": "Request body is not valid JSON.",
                    "status": 400,
                }
            ),
            400,
        )

    if request.json.get("schemas") == ["urn:ietf:params:scim:api:messages:2.0:BulkRequest"]:
        operations = request.json.get("Operations")
        results = []
        for op in operations:
            requestpath = op["path"]
            method = op["method"]
            data = op.get("data")
            bulkID = op.get("bulkId")

            environ = EnvironBuilder(
                path=requestpath,method=method,json=data,environ_base=request.environ).get_environ()

            with current_app.request_context(environ):
                try:
                    # Pre process Request
                    rv = current_app.preprocess_request()

                    if rv is None:
                        # Main Dispatch
                        rv = current_app.dispatch_request()

                except Exception as e:
                    rv = current_app.handle_user_exception(e)

                response = current_app.make_response(rv)

                # Post process Request
                response = current_app.process_response(response)

            if response.json is not None:
                json = dict(response.json)
                json["operation"] = op["operation"]
                if bulkID is not None:
                    results.append({bulkID: json})
                results.append(json)

                if json["status"] == "FAILURE":
                    break

        return make_response(jsonify({"status": "SUCCESS", "operations": results}), 200)

    else:
        return make_response(
            jsonify(
                {
                    "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Error"],
                    "scimType": "invalidSyntax",
                    "detail": "Request body is not valid JSON.",
                    "status": 400,
                }
            ),
            400,
        )
