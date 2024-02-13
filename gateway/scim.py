# Copyright (c) 2023, Cisco Systems, Inc. and/or its affiliates.
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
from models import EndpointApp, BleDevice, CoreDevice, OnboardingAppKey
from util import make_hash
from scim_ble import ble_create_device,ble_update_device
from scim_error import blow_an_error

scim_app = Blueprint("scim", __name__, url_prefix="/scim/v2")

def authenticate_user(func):
    """Verify x-api-key"""

    @wraps(func)
    def check_apikey(*args, **kwargs):
        client_cert = request.environ.get('peercert')
        if client_cert:
            return func(*args, **kwargs)

        api_key = request.headers.get("X-Api-Key")
        if api_key and bool(OnboardingAppKey.query.filter_by(key_val=api_key).first()):
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
        return blow_an_error("Request body is not valid JSON.",400)

    schemas = request.json.get("schemas")

    # Add device core object
    try:
        entry = CoreDevice(
            device_id=request.json.get("id"),
            schemas=request.json["schemas"],
            device_display_name=request.json["deviceDisplayName"],
            admin_state=request.json["adminState"],
            created_time=datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
        )
        session.add(entry)
        session.commit()
        core=entry.serialize()
    except Exception as e:
        return blow_an_error(str(e),400)

    # Dispatch to appropriate function
    if 'urn:ietf:params:scim:schemas:extension:ble:2.0:Device' in schemas:
        ble_extensions= ble_create_device(request,core)
        core.update(ble_extensions)
    else:
        return blow_an_error("Extension not implemented.",501)

    return make_response(jsonify(core),201)


@scim_app.route("/Devices/<string:device_id>", methods=["GET"])
@authenticate_user
def get_user(device_id):
    """
    SCIM API: Retrieve user data by ID and onboardApp parameters.
    If not found, a "User not found" response with a status code of 404
    is returned.
    """
    entry = session.get(CoreDevice,device_id)
    if not entry:
        return blow_an_error("Device not found",404)

    core=entry.serialize()
    entry = session.get(BleDevice,device_id)
    if entry:
        core.update(entry.serialize())
    return jsonify(entry)


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

        entries = CoreDevice.query.filter_by(device_mac_address=filter_value).first()

        if not entries:
            entries = []
        else:
            entries = [entries]

    else:
        entries = CoreDevice.query.paginate(
            page=start_index, per_page=count, error_out=False).items

    serialized_entries=[]
    for entry in entries:
        serialized_entry=entry.serialized()
        ble_entry=session.get(BleDevice,entry.device_id)
        if ble_entry:
            serialized_entry.update(ble_entry.serialize())
        serialized_entries.append(serialized_entry)


    return make_response(
        jsonify(
            {
                "schemas": ["urn:ietf:params:scim:api:messages:2.0:ListResponse"],
                "totalResults": len(entries),
                "startIndex": start_index,
                "itemsPerPage": len(entries),
                "Resources": serialized_entries,
            }
        ),
        200,
    )


@scim_app.route("/Devices/<string:entry_id>", methods=["PUT"])
@authenticate_user
def update_entry(entry_id):
    """
    Function to retrieve SCIM device data based on parameters like start
    index, count, and filters.

    Returns a JSON response with a list of serialized devices.
    """
    if not request.json:
        return blow_an_error("Request body is not valid JSON.",400)

    entry: CoreDevice = session.get(CoreDevice,entry_id)

    if not entry:
        return blow_an_error("Device not found",404)

    entry.id = request.json.get("id")
    entry.device_display_name = request.json.get("deviceDisplayName")
    entry.admin_state = request.json.get("adminState")
    entry.modified_time = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
    session.commit()
    core=entry.serialize()
    schemas = request.json["schemas"]
    if 'urn:ietf:params:scim:schemas:extension:ble:2.0:Device' in schemas:

        ble_json=request.json[
            "urn:ietf:params:scim:schemas:extension:ble:2.0:Device"]
        ble_entry=ble_update_device(ble_json,core)
    else:
        return blow_an_error("Extension not implemented.",501)

    ble_extension=ble_entry.serialize(core)
    core.update(ble_extension)
    return make_response(jsonify(core),200)

@scim_app.route("/Devices/<string:entry_id>", methods=["DELETE"])
@authenticate_user
def delete_device(entry_id):
    """Delete SCIM User"""
    entry = session.get(CoreDevice,entry_id)
    if not entry:
        return blow_an_error("Device not found",404)
    session.delete(entry)
    ble_entry = session.get(BleDevice,entry_id)
    if ble_entry:
        session.delete(ble_entry)
    session.commit()
    return make_response("", 204)


@scim_app.route("/EndpointApps/<string:id>", methods=["GET"])
@authenticate_user
def get_endpoint(device_id):
    """Get SCIM Endpoint"""
    endpoint_app = session.scalar(
        select(EndpointApp).filter_by(id=device_id))
    if not endpoint_app:
        return blow_an_error("Endpoint App not found",404)

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
        return blow_an_error("Request body is not valid JSON.",400)

    # check if endpoint app already exists
    endpoint_app = session.scalar(select(EndpointApp).filter_by(
        applicationName=request.json.get("applicationName")))

    if endpoint_app:
        return blow_an_error("Endpoint App already exists",400)

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
    endpoint_app = session.get(EndPointApp,device_id)
    if not endpoint_app:
        return blow_an_error("Endpoint App not found",404)

    session.delete(endpoint_app)
    session.commit()
    return make_response("", 204)


@scim_app.route("/Bulk", methods=["POST"])
@authenticate_user
def bulk_command():
    """ Processes SCIM bulk requests, handles operations, and returns summarized results. """
    if request.json is None:
        return blow_an_error("Request body is not valid JSON.",400)

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

    return blow_an_error("Request body is not valid JSON.",400)
