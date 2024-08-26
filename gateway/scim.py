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
import json
from functools import wraps
from flask import Blueprint, jsonify, make_response, request, current_app
from sqlalchemy import select
from werkzeug.test import EnvironBuilder
from tiedie_exceptions import DeviceExists, MABNotSupported, SchemaError, \
    ISEError, FDONotSupported
from scim_extensions import scim_ext_create, scim_ext_update, scim_ext_delete
from database import session
from models import EndpointApp, Device, OnboardingAppKey
from util import make_hash
from scim_ble import ble_get_filtered_entries
from scim_ethermab import ethermab_get_filtered_entries
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


def create_device_object(req,endpoint_apps,schemas,dev_id):
    """
    Create an object and return it to the main create routine.
    This is split because pylint doesn't like long routines.
    Sigh.
    """

    entry = Device(
        schemas=req.json["schemas"],
        display_name=req.json["displayName"],
        active=req.json["active"],
        endpoint_apps=endpoint_apps,
        created_time=datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
    )

    for ext in scim_ext_create:
        ext(schemas, entry, req, dev_id)

    if schemas:
        raise SchemaError("not supported: " + json.dumps(schemas))
    return entry


# SCIM Implementation


@scim_app.route('/Devices', methods=['POST'])
@authenticate_user
def create_device():
    """
    This code defines a SCIM API endpoint for creating users,
    extracts data from the request JSON, and stores user information in a database.
    """
    # Get the request json and check if it is valid
    try:
        if not isinstance(request.json["schemas"],list):
            return blow_an_error("schemas is not a list",400)
    except KeyError:
        return blow_an_error("Schema Error",400)

    schemas = request.json["schemas"].copy()
    device_id=request.json.get("id")

    if "urn:ietf:params:scim:schemas:core:2.0:Device" in schemas:
        schemas.remove("urn:ietf:params:scim:schemas:core:2.0:Device")
    else:
        return blow_an_error("SCIM Device Schema Required", 400)

    if device_id:
        return blow_an_error("Specifying id on create not permitted", 400)

    device_id = uuid.uuid4()

    endpoint_apps = None
    appextschema = \
        'urn:ietf:params:scim:schemas:extension:endpointAppsExt:2.0:Device'
    endpoint_apps_ext = request.json.get(appextschema, None)
    if endpoint_apps_ext and appextschema in schemas:
        schemas.remove(appextschema)
        applications = endpoint_apps_ext.get("applications")
        endpoint_app_ids = [app.get("value") for app in applications]
        # Select all endpoint apps from the database
        endpoint_apps = session.scalars(select(EndpointApp).filter(
            EndpointApp.id.in_(endpoint_app_ids))).all()
    elif appextschema in schemas:
        return blow_an_error(
            "endpointAppExt in schema, but no associated object.", 400)

    # Add device core object
    try:
        entry = create_device_object(request,endpoint_apps,schemas,device_id)
        session.add(entry)
        session.commit()

        core=entry.serialize()
        return make_response(jsonify(core),201)
    except DeviceExists:
        response= blow_an_error("Device already exists", 409,"uniqueness")
    except MABNotSupported:
        response = blow_an_error("MAB not supported.", 403,scim_code = None)
    except FDONotSupported:
        response = blow_an_error("FDO not supported", 403, scim_code = None)
    except SchemaError as e:
        response = blow_an_error(str(e),501)
    except ISEError as e:
        response = blow_an_error(str(e), 400)
    except Exception as e:
        response = blow_an_error(str(e),400)
    return response


@scim_app.route("/Devices/<string:device_id>", methods=["GET"])
@authenticate_user
def read_device(device_id):
    """
    SCIM API: Retrieve user data by ID and onboardApp parameters.
    If not found, a "User not found" response with a status code of 404
    is returned.
    """
    entry = session.get(Device,device_id)
    if not entry:
        return blow_an_error("Device not found",404)

    return jsonify(entry.serialize())


@scim_app.route("/Devices", methods=["GET"])
@authenticate_user
def read_devices():
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

        ble_entries = ble_get_filtered_entries(filter_value)
        mab_entries = ethermab_get_filtered_entries(filter_value)

        entries = []
        if ble_entries:
            for ble_entry in ble_entries:
                entries.append(ble_entry.device)
        if mab_entries:
            for mab_entry in mab_entries:
                entries.append(mab_entry.device)
    else:
        entries = Device.query.paginate(
            page=start_index, per_page=count, error_out=False).items

    serialized_entries=[]
    for entry in entries:
        serialized_entry=entry.serialize()
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
def update_device(entry_id):
    """
    Function to retrieve SCIM device data based on parameters like start
    index, count, and filters.

    Returns a JSON response with a list of serialized devices.
    """
    if not request.json:
        return blow_an_error("Request body is not valid JSON.",400)

    entry: Device = session.get(Device,entry_id)

    if not entry:
        return blow_an_error("Device not found",404)

    try:
        entry.device_id = request.json.get("id")
        entry.display_name = request.json.get("displayName")
        entry.active = request.json.get("active")
        entry.modified_time = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
        for ext in scim_ext_update:
            ext(entry,request)

        session.commit()
    except Exception as e:
        return blow_an_error(str(e),400)

    return make_response(jsonify(entry.serialize()),200)

@scim_app.route("/Devices/<string:entry_id>", methods=["DELETE"])
@authenticate_user
def delete_device(entry_id):
    """Delete SCIM Device"""
    entry = session.get(Device,entry_id)
    if not entry:
        return blow_an_error("Device not found",404)
    try:
        for ext in scim_ext_delete:
            ext(entry_id)
    except Exception as e:
        return make_response(str(e),400)
    session.delete(entry)
    session.commit()
    return make_response("", 204)

@scim_app.route("/EndpointApps/<string:id>", methods=["GET"])
@authenticate_user
def read_endpoint(endpoint_id):
    """Get SCIM Endpoint"""
    endpoint_app = session.scalar(
        select(EndpointApp).filter_by(id=endpoint_id))
    if not endpoint_app:
        return blow_an_error("Endpoint App not found",404)

    return make_response(jsonify(endpoint_app.serialize()), 200)


@scim_app.route("/EndpointApps", methods=["GET"])
@authenticate_user
def read_endpoints():
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
    certificate_info = request.json.get("certificateInfo", None)
    if certificate_info is None:
        endpoint_app.clientToken = uuid.uuid4()  # type: ignore
        if endpoint_app.applicationType == "telemetry":
            endpoint_app.password = make_hash(str(endpoint_app.clientToken))
    else:
        endpoint_app.rootCA = certificate_info.get("rootCA")
        endpoint_app.subjectName = certificate_info.get("subjectName")
    endpoint_app.createdTime = datetime.datetime.now()
    endpoint_app.modifiedTime = datetime.datetime.now()

    session.add(endpoint_app)
    session.commit()

    return make_response(jsonify(endpoint_app.serialize()), 201)


@scim_app.route("/EndpointApps/<string:id>", methods=["DELETE"])
@authenticate_user
def delete_endpoint(device_id):
    """ Deletes SCIM endpoint app by ID, handles not-found case, returns responses. """
    endpoint_app = session.get(EndpointApp,device_id)
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
                jn = dict(response.json)
                jn["operation"] = op["operation"]
                if bulk_id is not None:
                    results.append({bulk_id: json})
                results.append(json)

                if json["status"] == "FAILURE":
                    break

        return make_response(jsonify({"status": "SUCCESS", "operations": results}), 200)

    return blow_an_error("Request body is not valid JSON.",400)
