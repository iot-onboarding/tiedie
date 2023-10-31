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
from flask import Blueprint, jsonify, make_response, request, current_app
from sqlalchemy import select
from werkzeug.test import EnvironBuilder
from database import session
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
    deviceID = request.json.get("id")

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
            id=deviceID,
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
    If not found, a "User not found" response with a status code of 404
    is returned.
    """
    onboarding_app = request.args["onboardApp"]
    user = User.query.filter_by(user_id=user_id).filter_by(endpointApps=onboarding_app).first()
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


@scim_app.route("/Devices", methods=["GET"])
@authenticate_user
def get_devices():
    """Get SCIM Devices"""
    start_index = 1
    count = None

    if "start_index" in request.args:
        start_index = int(request.args["startIndex"])

    if "count" in request.args:
        count = int(request.args["count"])

    if "filter" in request.args:
        single_filter = request.args["filter"].split(" ")
        filter_value = single_filter[2].strip('"')

        users = User.query.filter_by(deviceMacAddress=filter_value).first()

        if not users:
            users = []
        else:
            users = [users]

    else:
        users = User.query.paginate(
            page=start_index, per_page=count, error_out=False).items

    serialized_users = [e.serialize() for e in users]

    return make_response(
        jsonify(
            {
                "schemas": ["urn:ietf:params:scim:api:messages:2.0:ListResponse"],
                "totalResults": len(users),
                "startIndex": start_index,
                "itemsPerPage": len(users),
                "Resources": serialized_users,
            }
        ),
        200,
    )


@scim_app.route("/Devices/<string:user_id>", methods=["PUT"])
@authenticate_user
def update_user(user_id):
    """
    Function to retrieve SCIM device data based on parameters like start
    index, count, and filters.

    Returns a JSON response with a list of serialized devices.
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

    user = User.query.get(user_id)

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
    user.pairingOOBRN = \
        request.json["urn:ietf:params:scim:schemas:extension:ble:2.0:Device"][
            "urn:ietf:params:scim:schemas:extension:pairingOOB:2.0:Device"].get("randNumber")
    user.modTime = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")

    session.commit()
    return make_response(jsonify(user.serialize()), 200)


@scim_app.route("/Devices/<string:user_id>", methods=["DELETE"])
@authenticate_user
def delete_user(user_id):
    """Delete SCIM User"""
    user = User.query.get(user_id)
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
    session.delete(user)
    session.commit()
    return make_response("", 204)


@scim_app.route("/EndpointApps/<string:id>", methods=["GET"])
@authenticate_user
def get_endpoint(id):
    """Get SCIM Endpoint"""
    endpoint_app = session.scalar(select(EndpointApp).filter_by(id=id))
    if not endpoint_app:
        return make_response(
            jsonify(
                {
                    "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Error"],
                    "detail": "Endpoint App not found",
                    "status": 404,
                }
            ),
            404,
        )
    return make_response(jsonify(endpoint_app.serialize()), 200)


@scim_app.route("/EndpointApps", methods=["GET"])
@authenticate_user
def get_endpoints():
    """Get SCIM Endpoint"""
    start_index = 1
    count = None

    if "start_index" in request.args:
        start_index = int(request.args["startIndex"])

    if "count" in request.args:
        count = int(request.args["count"])

    if "filter" in request.args:
        single_filter = request.args["filter"].split(" ")
        filter_value = single_filter[2].strip('"')

        endpoint_apps = EndpointApp.query.filter_by(
            applicationName=filter_value).first()

        if not endpoint_apps:
            endpoint_apps = []
        else:
            endpoint_apps = [endpoint_apps]

    else:
        endpoint_apps = EndpointApp.query.paginate(
            page=start_index, per_page=count, error_out=False).items

    serialized_endpoint_apps = [e.serialize() for e in endpoint_apps]

    return make_response(
        jsonify(
            {
                "schemas": ["urn:ietf:params:scim:api:messages:2.0:ListResponse"],
                "totalResults": len(endpoint_apps),
                "startIndex": start_index,
                "itemsPerPage": len(endpoint_apps),
                "Resources": serialized_endpoint_apps,
            }
        ),
        200,
    )


@scim_app.route('/EndpointApps', methods=['POST'])
@authenticate_user
def create_endpoint():
    """ Creates SCIM endpoint app; checks validity, avoids duplicates, returns response. """
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

    # check if endpoint app already exists
    endpoint_app = session.scalar(select(EndpointApp).filter_by(
        applicationName=request.json.get("applicationName")))

    if endpoint_app:
        return make_response(
            jsonify(
                {
                    "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Error"],
                    "scimType": "invalidSyntax",
                    "detail": "Endpoint App already exists",
                    "status": 400,
                }
            ),
            400,
        )

    endpoint_app = EndpointApp()
    endpoint_app.applicationType = request.json.get("applicationType")
    endpoint_app.applicationName = request.json.get("applicationName")
    endpoint_app.certificateInfo = request.json.get("certificateInfo", None)
    if endpoint_app.certificateInfo is None:
        endpoint_app.clientToken = uuid.uuid4()  # type: ignore
        if endpoint_app.applicationType == "telemetry":
            endpoint_app.password = make_hash(str(endpoint_app.clientToken))
    endpoint_app.createdTime = datetime.datetime.now()
    endpoint_app.modifiedTime = datetime.datetime.now()

    session.add(endpoint_app)
    session.commit()

    return make_response(jsonify(endpoint_app.serialize()), 201)


@scim_app.route("/EndpointApps/<string:id>", methods=["DELETE"])
@authenticate_user
def delete_endpoint(id):
    """ Deletes SCIM endpoint app by ID, handles not-found case, returns responses. """
    endpoint_app = EndpointApp.query.get(id)
    if not endpoint_app:
        return make_response(
            jsonify(
                {
                    "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Error"],
                    "detail": "Endpoint App not found",
                    "status": 404,
                }
            ),
            404,
        )
    session.delete(endpoint_app)
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
    print(request.json.get("schemas"))
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
