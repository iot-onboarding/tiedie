# Copyright (c) 2023, Cisco and/or its affiliates.
# All rights reserved.
# See license in distribution for details.

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
    device_display_name = request.json.get("deviceDisplayName")
    admin_state = request.json.get("adminState")
    version_support = request.json["urn:ietf:params:scim:schemas:extension:ble:2.0:Device"].get(
        "versionSupport")
    device_mac_address = request.json["urn:ietf:params:scim:schemas:extension:ble:2.0:Device"].get(
        "deviceMacAddress")
    is_random = request.json["urn:ietf:params:scim:schemas:extension:ble:2.0:Device"].get(
        "isRandom")
    separate_broadcast_address = request.json[
        "urn:ietf:params:scim:schemas:extension:ble:2.0:Device"].get(
        "separateBroadcastAddress", [])
    irk = request.json["urn:ietf:params:scim:schemas:extension:ble:2.0:Device"].get(
        "irk", "")
    pairing_methods = request.json["urn:ietf:params:scim:schemas:extension:ble:2.0:Device"].get(
        "pairingMethods", [])
    pairing_null = request.json["urn:ietf:params:scim:schemas:extension:ble:2.0:Device"].get(
        "urn:ietf:params:scim:schemas:extension:pairingNull:2.0:Device")
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

    existing_device = User.query.filter_by(
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
        user = User(
            device_id=device_id,
            schemas=schemas,
            device_display_name=device_display_name,
            admin_state=admin_state,
            version_support=version_support,
            device_mac_address=device_mac_address,
            is_random=is_random,
            separate_broadcast_address=separate_broadcast_address,
            irk=irk,
            pairing_methods=pairing_methods,
            pairing_null=pairing_null,
            pairing_just_works_keys=pairing_just_works_key,
            pairing_pass_key=pairing_pass_key,
            pairing_oob_key=pairing_oob_key,
            pairing_oobrn=pairing_oobrn,
            endpoint_apps=endpoint_apps,
            created_time=datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
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

        users = User.query.filter_by(device_mac_address=filter_value).first()

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

    user: User = User.query.get(user_id)

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
def get_endpoint(device_id):
    """Get SCIM Endpoint"""
    endpoint_app = session.scalar(
        select(EndpointApp).filter_by(id=device_id))
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
def delete_endpoint(device_id):
    """ Deletes SCIM endpoint app by ID, handles not-found case, returns responses. """
    endpoint_app = EndpointApp.query.get(device_id)
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
            bulk_id = op.get("bulkId")

            environ = EnvironBuilder(
                path=requestpath,
                method=method,
                json=data,
                environ_base=request.environ
            ).get_environ()

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
                if bulk_id is not None:
                    results.append({bulk_id: json})
                results.append(json)

                if json["status"] == "FAILURE":
                    break

        return make_response(jsonify({"status": "SUCCESS", "operations": results}), 200)

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
