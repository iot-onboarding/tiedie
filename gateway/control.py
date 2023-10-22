# Copyright (c) 2023, Cisco and/or its affiliates.
# All rights reserved.
# See license in distribution for details.

import uuid
from http import HTTPStatus
from typing import Any
from functools import wraps
from flask import Blueprint, current_app, jsonify, make_response, request
from sqlalchemy import select
from werkzeug.test import EnvironBuilder
import werkzeug.serving
import OpenSSL
from access_point import get_ble_app
from database import db, session
from models import AdvTopic, DataAppTopic, EndpointApp, GattTopic, User, AdvFilter

control_app = Blueprint("control", __name__, url_prefix="/control")

ble_app = get_ble_app()


class PeerCertWSGIRequestHandler(werkzeug.serving.WSGIRequestHandler):
    def make_environ(self):
        environ = super(PeerCertWSGIRequestHandler, self).make_environ()
        x509_binary = self.connection.getpeercert(True)
        if x509_binary is None:
            environ['peercert'] = None
            return environ
        x509 = OpenSSL.crypto.load_certificate(  # type: ignore
            OpenSSL.crypto.FILETYPE_ASN1, x509_binary)  # type: ignore
        environ['peercert'] = x509
        return environ


def authenticate_user(func):
    """Verify x-api-key"""

    @wraps(func)
    def check_apikey(*args, **kwargs):
        global ble_app
        ble_app = get_ble_app()

        client_cert = request.environ['peercert']
        if client_cert:
            if session.scalar(select(EndpointApp).filter_by(applicationName=client_cert.get_subject().CN)) is not None:
                return func(*args, **kwargs)
            else:
                return make_response(jsonify({"error": "Unauthorized"}), 403)

        api_key = request.headers.get("X-Api-Key")

        if request.json is None:
            return make_response(jsonify({"error": "Unauthorized"}), 403)

        control_app = request.json.get("controlApp")
        endpoint_app = session.scalar(select(EndpointApp).
                                      filter_by(applicationName=control_app))
        print(endpoint_app.clientToken, api_key, control_app)
        if endpoint_app is None or api_key is None or api_key != endpoint_app.clientToken:
            return make_response(jsonify({"error": "Unauthorized"}), 403)

        return func(*args, **kwargs)
    return check_apikey


@control_app.route('/connectivity/connect', methods=['POST'])
@authenticate_user
def connect():
    if not request.json:
        return jsonify({"status": "FAILURE"}), HTTPStatus.BAD_REQUEST

    technology = request.json.get("technology")
    uuid = request.json.get("id")

    if technology != "ble" or "ble" not in request.json:
        return jsonify({"status": "FAILURE"}), HTTPStatus.BAD_REQUEST

    ble = request.json.get("ble")
    services = ble["services"]
    retries = request.json.get("retries")
    
    device = session.execute(select(User).filter_by(id=uuid)).scalar_one()

    resp, respcode = ble_app.connect(device.deviceMacAddress, services, retries)

    resp = resp.get_json()
    resp['id'] = uuid
    return jsonify(resp), respcode


@control_app.route('/connectivity/disconnect', methods=['POST'])
@authenticate_user
def disconnect():
    if not request.json:
        return jsonify({"status": "FAILURE"}), HTTPStatus.BAD_REQUEST

    uuid = request.json.get("id")

    device = session.execute(select(User).filter_by(id=uuid)).scalar_one()

    resp, respcode =  ble_app.disconnect(device.deviceMacAddress)
    resp = resp.get_json()
    resp['id'] = uuid
    return resp, respcode

@control_app.route('/data/discover', methods=['POST'])
@authenticate_user
def discover():
    if not request.json:
        return jsonify({"status": "FAILURE"}), HTTPStatus.BAD_REQUEST
    
    uuid = request.json.get("id")


    device = session.execute(select(User).filter_by(id=uuid)).scalar_one()

    ble = request.json.get("ble")
    services = ble["services"]

    resp, respcode = ble_app.discover(device.deviceMacAddress, services)

    resp = resp.get_json()
    resp['id'] = uuid

    return jsonify(resp), respcode


@control_app.route('/data/read', methods=['POST'])
@authenticate_user
def read():
    if not request.json:
        return jsonify({"status": "FAILURE"}), HTTPStatus.BAD_REQUEST

    technology = request.json.get("technology")
    uuid = request.json.get("id")

    if technology != "ble" or "ble" not in request.json:
        return jsonify({"status": "FAILURE"}), HTTPStatus.BAD_REQUEST

    ble = request.json.get("ble")
    serviceUUID = ble["serviceID"].lower()
    characteristicUUID = ble["characteristicID"].lower()

    device = session.execute(select(User).filter_by(id=uuid)).scalar_one()

    resp, respcode = ble_app.read(device.deviceMacAddress, serviceUUID, characteristicUUID)

    resp = resp.get_json()
    resp['id'] = uuid

    return resp, respcode

@control_app.route('/data/write', methods=['POST'])
@authenticate_user
def write():
    if not request.json:
        return jsonify({"status": "FAILURE"}), HTTPStatus.BAD_REQUEST

    technology = request.json.get("technology")
    uuid = request.json.get("id")

    if technology != "ble" or "ble" not in request.json:
        return jsonify({"status": "FAILURE"}), HTTPStatus.BAD_REQUEST

    ble = request.json.get("ble")
    serviceUUID = ble["serviceID"].lower()
    characteristicUUID = ble["characteristicID"].lower()
    value = request.json.get("value").lower()

    device = session.scalar(select(User).filter_by(id=uuid))

    if device is None:
        return jsonify({"status": "FAILURE"}), HTTPStatus.BAD_REQUEST

    resp, respcode =  ble_app.write(device.deviceMacAddress, serviceUUID, characteristicUUID, value)

    resp = resp.get_json()
    resp['id'] = uuid

    return resp, respcode


@control_app.route('/data/subscribe', methods=['POST'])
@authenticate_user
def subscribe():
    if not request.json:
        return jsonify({"status": "FAILURE"}), HTTPStatus.BAD_REQUEST

    technology = request.json.get("technology")
    uuid = request.json.get("id")

    if technology != "ble" or "ble" not in request.json:
        return jsonify({"status": "FAILURE"}), HTTPStatus.BAD_REQUEST

    ble = request.json.get("ble")
    serviceUUID = ble["serviceID"].lower()
    characteristicUUID = ble["characteristicID"].lower()

    device = session.scalar(select(User).filter_by(id=uuid))

    if device is None:
        return jsonify({"status": "FAILURE"}), HTTPStatus.BAD_REQUEST

    resp, respcode = ble_app.subscribe(device.deviceMacAddress, serviceUUID, characteristicUUID)

    resp = resp.get_json()
    resp['id'] = uuid

    return resp, respcode


@control_app.route('/data/unsubscribe', methods=['POST'])
@authenticate_user
def unsubscribe():
    if not request.json:
        return jsonify({"status": "FAILURE"}), HTTPStatus.BAD_REQUEST

    technology = request.json.get("technology")
    uuid = request.json.get("id")

    if technology != "ble" or "ble" not in request.json:
        return jsonify({"status": "FAILURE"}), HTTPStatus.BAD_REQUEST

    ble = request.json.get("ble")
    serviceUUID = ble["serviceID"].lower()
    characteristicUUID = ble["characteristicID"].lower()

    device = session.scalar(select(User).filter_by(id=uuid))

    if device is None:
        return jsonify({"status": "FAILURE"}), HTTPStatus.BAD_REQUEST

    resp, respcode =  ble_app.unsubscribe(device.deviceMacAddress, serviceUUID, characteristicUUID)

    resp = resp.get_json()
    resp['id'] = uuid

    return resp, respcode


@control_app.route('/registration/registerTopic', methods=['POST'])
@authenticate_user
def register_topic():
    if not request.json:
        return jsonify({"status": "FAILURE"}), HTTPStatus.BAD_REQUEST

    technology = request.json.get("technology")
    id = request.json.get("id", None)

    if technology != "ble" or "ble" not in request.json:
        return jsonify({"status": "FAILURE"}), HTTPStatus.BAD_REQUEST

    topic = request.json["topic"]
    data_format = request.json.get("dataFormat", "default")
    ble = request.json["ble"]

    type = ble["type"]

    if type == "gatt":
        serviceUUID = ble["serviceID"].lower()
        characteristicUUID = ble["characteristicID"].lower()

        devices = [session.execute(select(User).filter_by(id=id)).scalar_one()]

        gatt_topic = GattTopic(
            topic, serviceUUID, characteristicUUID, data_format, devices)
        session.merge(gatt_topic)
        session.commit()
    else:
        if id:
            device = [session.execute(select(User).filter_by(id=id)).scalar_one()]

            if device is None:
                return jsonify({"status": "FAILURE"}), HTTPStatus.BAD_REQUEST

            adv_topic = AdvTopic(topic, data_format, device)
            session.merge(adv_topic)
            session.commit()
        else:
            filter_type = ble.get("filterType", "allow")
            filters = ble.get("filters", [])

            if len(filters) > 0:
                adv_filters: list[AdvFilter] = []
                for filter in filters:
                    adv_filter = AdvFilter(topic, filter.get(
                        "mac", "*"), filter.get("adType", "*"), filter.get("adData", "*"))
                    adv_filters.append(adv_filter)

                # if adv_topic already exists, delete all filters and add new ones
                adv_topic = session.scalar(
                    select(AdvTopic).filter_by(topic=topic))
                if adv_topic is not None:
                    session.query(AdvFilter).filter_by(topic=topic).delete()

                adv_topic = AdvTopic(
                    topic, data_format, filter_type=filter_type, filters=adv_filters)
                session.merge(adv_topic)
            else:
                adv_topic = AdvTopic(topic, data_format)
                session.merge(adv_topic)
            session.commit()

    return jsonify({"status": "SUCCESS", "id": uuid.uuid4(), "requestID": uuid.uuid4(), "topic": topic}), HTTPStatus.OK


@control_app.route('/registration/unregisterTopic', methods=['POST'])
@authenticate_user
def unregister_topic():
    if not request.json:
        return jsonify({"status": "FAILURE"}), HTTPStatus.BAD_REQUEST

    topic = request.json["topic"]

    gatt_topic = session.scalar(select(GattTopic).filter_by(topic=topic))

    adv_topic = session.scalar(select(AdvTopic).filter_by(topic=topic))

    if gatt_topic is None and adv_topic is None:
        return jsonify({"status": "FAILURE"}), HTTPStatus.BAD_REQUEST

    if gatt_topic is not None and "ids" in request.json:
        uuids = request.json["ids"]

        for device in gatt_topic.devices:
            if str(device.id) in uuids:
                gatt_topic.devices.remove(device)

        if len(gatt_topic.devices) == 0:
            session.delete(gatt_topic)

        session.commit()

    if adv_topic is not None and "ids" in request.json:
        uuids = request.json["ids"]

        if len(adv_topic.devices) > 0:
            for device in adv_topic.devices:
                if str(device.id) in uuids:
                    adv_topic.devices.remove(device)

        if len(adv_topic.devices) == 0:
            session.delete(adv_topic)

        session.commit()

    if adv_topic is not None and adv_topic.onboarded is False:
        if len(adv_topic.filters) > 0:
            session.query(AdvFilter).filter_by(topic=topic).delete()

        session.delete(adv_topic)
        session.commit()

    return jsonify({"status": "SUCCESS", "id": uuid.uuid4(), "requestID": uuid.uuid4(), "topic": topic}), HTTPStatus.OK

@control_app.route('/registration/registerDataApp', methods=['POST'])
@authenticate_user
def register_data_app():
    if not request.json:
        return jsonify({"status": "FAILURE"}), HTTPStatus.BAD_REQUEST

    topic = request.json.get("topic")
    data_apps = request.json.get("dataApps")

    for data_app in data_apps:
        data_app_topic = DataAppTopic(data_app['dataAppID'], topic)
        session.merge(data_app_topic)

    session.commit()

    return jsonify({"status": "SUCCESS", "id": uuid.uuid4(), "requestID": uuid.uuid4(), "topic": topic}), HTTPStatus.OK


@control_app.route('/registration/unregisterDataApp', methods=['POST'])
@authenticate_user
def unregister_data_app():
    if not request.json:
        return jsonify({"status": "FAILURE"}), HTTPStatus.BAD_REQUEST

    topic = request.json.get("topic")
    data_apps = request.json.get("dataApps")

    for data_app in data_apps:
        data_app_topic = session.scalar(
            select(DataAppTopic).filter_by(data_app_id=data_app, topic=topic))

        if data_app_topic is not None:
            session.delete(data_app_topic)

    session.commit()

    return jsonify({"status": "SUCCESS", "id": uuid.uuid4(), "requestID": uuid.uuid4(), "topic": topic}), HTTPStatus.OK


@control_app.route('/bulk', methods=['POST'])
@authenticate_user
def bulk():
    if not request.json:
        return jsonify({"status": "FAILURE"}), HTTPStatus.BAD_REQUEST

    technology = request.json.get("technology")
    if technology != "ble":
        return jsonify({"status": "FAILURE"}), HTTPStatus.BAD_REQUEST

    uuid = request.json.get("id")
    control_app = request.json.get("controlApp")

    operations = request.json.get("operations", [])

    responses: list[Any] = []

    for operation in operations:
        path = "/control" + operation["operation"]
        method = "POST"
        data = {
            "technology": technology,
            "id": uuid,
            "controlApp": control_app,
            "ble": operation["ble"]
        }

        environ = EnvironBuilder(
            path=path, method=method, json=data, environ_base=request.environ).get_environ()

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
            json["operation"] = operation["operation"]
            responses.append(json)

            if json["status"] == "FAILURE":
                break

    return jsonify({"status": "SUCCESS", "operations": responses}), HTTPStatus.OK
