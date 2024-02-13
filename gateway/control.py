# Copyright (c) 2023, Cisco Systems, Inc. and/or its affiliates.
# All rights reserved.
# See LICENSE file in this distribution.
# SPDX-License-Identifier: Apache-2.0

"""

This module creates a Flask Blueprint for controlling Bluetooth Low
Energy (BLE) devices, handling connections, data operations, and topic
registrations with authentication.

"""

from uuid import uuid4
from http import HTTPStatus
from typing import Any
from functools import wraps
from flask import Blueprint, current_app, jsonify, make_response, redirect, request, url_for
from sqlalchemy import select
from werkzeug.test import EnvironBuilder
import werkzeug.serving
import OpenSSL
from access_point import BleConnectOptions
from ap_factory import ble_ap
from database import session
from models import (
    AdvTopic,
    ConnectionTopic,
    DataAppTopic,
    EndpointApp,
    GattTopic,
    BleDevice,
    AdvFilter
)

control_app = Blueprint("control", __name__, url_prefix="/nipc")


class PeerCertWSGIRequestHandler(werkzeug.serving.WSGIRequestHandler):
    """ Custom WSGI request handler to extract and provide peer certificates. """

    def make_environ(self):
        environ = super().make_environ()
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
        client_cert = request.environ['peercert']
        if client_cert:
            if session.scalar(
                select(EndpointApp)
                .filter_by(applicationName=client_cert.get_subject().CN)
            ) is not None:
                return func(*args, **kwargs)

            return make_response(jsonify({"error": "Unauthorized"}), 403)

        api_key = request.headers.get("X-Api-Key")
        if api_key is None:
            return make_response(jsonify({"error": "Unauthorized"}), 403)

        endpoint_app = session.scalar(select(EndpointApp).
                                      filter_by(clientToken=api_key))

        if endpoint_app is None:
            return make_response(jsonify({"error": "Unauthorized"}), 403)

        return func(*args, **kwargs)
    return check_apikey


@control_app.route('/connectivity/connection', methods=['GET'])
@authenticate_user
def get_connection():
    """ Get connection state for a device """
    return redirect(url_for('control.get_connection_by_id', device_id=request.args.get('id')))


@control_app.route('/connectivity/connection/id/<device_id>', methods=['GET'])
@authenticate_user
def get_connection_by_id(device_id: str):
    """ Get connection state for a device """
    device = session.execute(
        select(BleDevice).filter_by(id=device_id)).scalar_one_or_none()

    conn = ble_ap().get_connection(device.device_mac_address)

    if conn:
        return jsonify({"status": "SUCCESS"}), HTTPStatus.OK

    return jsonify({"status": "FAILURE", "reason": "Connection not found"}), HTTPStatus.OK


@control_app.route('/connectivity/connection/id/<device_id>', methods=['POST'])
@authenticate_user
def connect_by_id(device_id: str):
    """ Connect API """
    device = session.execute(
        select(BleDevice).filter_by(id=device_id)).scalar_one_or_none()

    return ble_ap().connect(device.device_mac_address,
                            BleConnectOptions(
                                [], False, 3600),
                            3)


@control_app.route('/connectivity/connection', methods=['POST'])
@authenticate_user
def connect():
    """ Connect API """
    if not request.json:
        return jsonify({"status": "FAILURE"}), HTTPStatus.BAD_REQUEST

    device_id = request.json.get("id")

    ble = request.json.get("ble")
    retries = request.json.get("retries", 3)
    services = ble.get("services", [])
    cached = ble.get("cached", False)
    cache_idle_purge = ble.get("cacheIdlePurge", 3600)

    device = session.execute(
        select(BleDevice).filter_by(id=device_id)).scalar_one_or_none()

    resp, respcode = ble_ap().connect(device.device_mac_address,
                                      BleConnectOptions(
                                          services, cached, cache_idle_purge),
                                      retries)

    return resp, respcode


@control_app.route('/connectivity/connection/id/<device_id>', methods=['DELETE'])
@authenticate_user
def disconnect_by_id(device_id: str):
    """ Disconnect API """
    device = session.execute(
        select(BleDevice).filter_by(id=device_id)).scalar_one_or_none()

    return ble_ap().disconnect(device.device_mac_address)


@control_app.route('/connectivity/connection', methods=['DELETE'])
@authenticate_user
def disconnect():
    """ Disconnect API """
    device_id = request.args.get("id")

    device = session.execute(
        select(BleDevice).filter_by(id=device_id)).scalar_one_or_none()

    return ble_ap().disconnect(device.device_mac_address)


@control_app.route('/connectivity/services/id/<device_id>', methods=['GET'])
@authenticate_user
def discover_by_id(device_id: str):
    """ Service discovery API """
    device = session.execute(
        select(BleDevice).filter_by(id=device_id)).scalar_one_or_none()

    return ble_ap().discover(device.device_mac_address,
                             BleConnectOptions(
                                 [], False, 3600), 3)


@control_app.route('/connectivity/services', methods=['GET'])
@authenticate_user
def discover():
    """ Service discovery API """
    if not request.args:
        return jsonify({"status": "FAILURE"}), HTTPStatus.BAD_REQUEST

    device_id = request.args.get("id")

    device = session.execute(
        select(BleDevice).filter_by(id=device_id)).scalar_one_or_none()

    services = request.args.getlist("ble[services][serviceID]")
    cached = request.args.get("ble[cached]", False)
    cache_idle_purge = request.args.get("ble[cacheIdlePurge]", 3600)
    retries = request.args.get("retries", 3)

    return ble_ap().discover(device.device_mac_address,
                             BleConnectOptions(
                                 services, cached, cache_idle_purge),
                             retries)


@control_app.route('/data/attribute', methods=['GET'])
@authenticate_user
def read():
    """ Function Read """
    if not request.args:
        return jsonify({"status": "FAILURE"}), HTTPStatus.BAD_REQUEST

    device_id = request.args.get("id")

    service_id = request.args["ble[serviceID]"].lower()
    characteristic_id = request.args["ble[characteristicID]"].lower()

    device = session.execute(
        select(BleDevice).filter_by(id=device_id)).scalar_one_or_none()

    resp, respcode = ble_ap().read(
        device.device_mac_address, service_id, characteristic_id)

    return resp, respcode


@control_app.route('/data/attribute', methods=['POST', 'PUT'])
@authenticate_user
def write():
    """ Function Write """
    if not request.json:
        return jsonify({"status": "FAILURE"}), HTTPStatus.BAD_REQUEST

    device_id = request.json.get("id")

    ble = request.json.get("ble")
    service_id = ble["serviceID"].lower()
    characteristic_id = ble["characteristicID"].lower()
    value = request.json["value"].lower()

    device = session.scalar(select(BleDevice).filter_by(id=device_id))

    if device is None:
        return jsonify({"status": "FAILURE"}), HTTPStatus.BAD_REQUEST

    resp, respcode = ble_ap().write(
        device.device_mac_address, service_id, characteristic_id, value)

    return resp, respcode


@control_app.route('/data/subscription', methods=['POST', 'PUT'])
@authenticate_user
def subscribe():
    """ This function subscribes a user device from a BLE service. """
    if not request.json:
        return jsonify({"status": "FAILURE"}), HTTPStatus.BAD_REQUEST

    device_id = request.json.get("id")

    ble = request.json.get("ble")
    service_id = ble["serviceID"].lower()
    characteristic_id = ble["characteristicID"].lower()

    device = session.scalar(select(BleDevice).filter_by(id=device_id))

    if device is None:
        return jsonify({"status": "FAILURE"}), HTTPStatus.BAD_REQUEST

    resp, respcode = ble_ap().subscribe(
        device.device_mac_address, service_id, characteristic_id)

    # optionally register a topic for the device
    topic = request.json.get("topic", None)

    if topic is not None:
        data_format = request.json.get("dataFormat", "default")

        service_id = ble["serviceID"].lower()
        characteristic_id = ble["characteristicID"].lower()

        device = session.execute(
            select(BleDevice).filter_by(id=device_id)).scalar_one_or_none()

        gatt_topic = GattTopic(
            topic, service_id, characteristic_id, data_format, [device])
        session.merge(gatt_topic)
        session.commit()

    return resp, respcode


@control_app.route('/data/subscription', methods=['DELETE'])
@authenticate_user
def unsubscribe():
    """ This function unsubscribes a user device from a BLE service. """
    if not request.json:
        return jsonify({"status": "FAILURE"}), HTTPStatus.BAD_REQUEST

    device_id = request.json.get("id")

    ble = request.json.get("ble")
    service_id = ble["serviceID"].lower()
    characteristic_id = ble["characteristicID"].lower()

    device = session.scalar(select(BleDevice).filter_by(id=device_id))

    if device is None:
        return jsonify({"status": "FAILURE"}), HTTPStatus.BAD_REQUEST

    resp, respcode = ble_ap().unsubscribe(
        device.device_mac_address, service_id, characteristic_id)

    return resp, respcode


@control_app.route('/registration/topic', methods=['POST', 'PUT'])
@authenticate_user
def register_topic():
    """ Function to register topic """
    if not request.json:
        return jsonify({"status": "FAILURE"}), HTTPStatus.BAD_REQUEST

    device_id = request.json.get("id", None)

    topic = request.json["topic"]
    data_format = request.json.get("dataFormat", "default")
    ble = request.json["ble"]

    ad_type = ble["type"]

    data_apps = request.json.get("dataApps", [])

    if ad_type == "gatt":
        service_id = ble["serviceID"].lower()
        characteristic_id = ble["characteristicID"].lower()

        device = session.execute(
            select(BleDevice).filter_by(id=device_id)).scalar_one_or_none()

        gatt_topic = GattTopic(
            topic, service_id, characteristic_id, data_format, [device])
        session.merge(gatt_topic)
        session.commit()
    elif ad_type == "connection_events":
        device = session.execute(
            select(BleDevice).filter_by(id=device_id)).scalar_one_or_none()

        if not device:
            return jsonify({"status": "FAILURE"}), HTTPStatus.BAD_REQUEST

        connection_topic = ConnectionTopic(topic, data_format, [device])

        session.merge(connection_topic)
        session.commit()
    elif ad_type == "advertisements":
        if device_id is not None:
            device = session.execute(
                select(BleDevice).filter_by(id=device_id)).scalar_one_or_none()

            if device is None:
                return jsonify({"status": "FAILURE"}), HTTPStatus.BAD_REQUEST

            adv_topic = AdvTopic(topic, data_format, [device])
            session.merge(adv_topic)
            session.commit()
        else:
            filter_type = ble.get("filterType", "allow")
            filters = ble.get("filters", [])

            if len(filters) > 0:
                adv_filters: list[AdvFilter] = []
                for topic_filter in filters:
                    adv_filter = AdvFilter(topic, topic_filter.get(
                        "mac", "*"),
                        topic_filter.get("adType", "*"),
                        topic_filter.get("adData", "*")
                    )
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

    for data_app in data_apps:
        data_app_id = data_app["dataAppID"]
        data_app_topic = DataAppTopic(data_app_id, topic)
        session.merge(data_app_topic)

    session.commit()

    ret_json = {"status": "SUCCESS",
                "id": uuid4(), "requestID": uuid4(), "topic": topic}
    return jsonify(ret_json), HTTPStatus.OK


@control_app.route('/registration/topic', methods=['DELETE'])
@authenticate_user
def unregister_topic():
    """ Function to unregister topic """
    if not request.args:
        return jsonify({"status": "FAILURE"}), HTTPStatus.BAD_REQUEST

    topic = request.args["topic"]

    gatt_topic = session.scalar(select(GattTopic).filter_by(topic=topic))

    adv_topic = session.scalar(select(AdvTopic).filter_by(topic=topic))

    if gatt_topic is None and adv_topic is None:
        return jsonify({"status": "FAILURE"}), HTTPStatus.BAD_REQUEST

    if gatt_topic is not None:
        for device in gatt_topic.devices:
            gatt_topic.devices.remove(device)

        session.delete(gatt_topic)

        session.commit()

    if adv_topic is not None:
        for device in adv_topic.devices:
            adv_topic.devices.remove(device)

        session.delete(adv_topic)

        session.commit()

    if adv_topic is not None and adv_topic.onboarded is False:
        if len(adv_topic.filters) > 0:
            session.query(AdvFilter).filter_by(topic=topic).delete()

        session.delete(adv_topic)
        session.commit()
    arg_json = {"status": "SUCCESS",
                "id": uuid4(), "requestID": uuid4(), "topic": topic}
    return jsonify(arg_json), HTTPStatus.OK


@control_app.route('/registration/topic', methods=['GET'])
@authenticate_user
def get_topic():
    """ Fetch registered topic information """
    topic = request.args.get("topic")

    gatt_topic = session.scalar(select(GattTopic).filter_by(topic=topic))

    adv_topic = session.scalar(select(AdvTopic).filter_by(topic=topic))

    if gatt_topic is None and adv_topic is None:
        return jsonify({"status": "FAILURE"}), HTTPStatus.BAD_REQUEST

    return jsonify({
        "status": "SUCCESS",
        "topics": [
            {
                "topic": topic
            }
        ]
    }), HTTPStatus.OK


@control_app.route('/registration/topic/<topic>', methods=['DELETE'])
@authenticate_user
def delete_topic_by_name(topic: str):
    """ Function to unregister topic """
    gatt_topic = session.scalar(select(GattTopic).filter_by(topic=topic))

    adv_topic = session.scalar(select(AdvTopic).filter_by(topic=topic))

    if gatt_topic is None and adv_topic is None:
        return jsonify({"status": "FAILURE"}), HTTPStatus.BAD_REQUEST

    if gatt_topic is not None:
        for device in gatt_topic.devices:
            gatt_topic.devices.remove(device)

        session.delete(gatt_topic)

        session.commit()

    if adv_topic is not None:
        for device in adv_topic.devices:
            adv_topic.devices.remove(device)

        session.delete(adv_topic)

        session.commit()

    if adv_topic is not None and adv_topic.onboarded is False:
        if len(adv_topic.filters) > 0:
            session.query(AdvFilter).filter_by(topic=topic).delete()

        session.delete(adv_topic)
        session.commit()

    return jsonify({"status": "SUCCESS"}), HTTPStatus.OK


@control_app.route('/registration/topic/<topic>', methods=['GET'])
@authenticate_user
def get_topic_by_name(topic: str):
    """ Fetch registered topic information """
    gatt_topic = session.scalar(select(GattTopic).filter_by(topic=topic))

    adv_topic = session.scalar(select(AdvTopic).filter_by(topic=topic))

    if gatt_topic is None and adv_topic is None:
        return jsonify({"status": "FAILURE"}), HTTPStatus.BAD_REQUEST

    return jsonify({
        "status": "SUCCESS",
        "topics": [
            {
                "topic": topic
            }
        ]
    }), HTTPStatus.OK


@control_app.route('/registration/topic/data-app/<data_app_id>', methods=['DELETE'])
@authenticate_user
def delete_topics_by_data_app(data_app_id: str):
    """ Function to unregister topic """
    data_app_topics = session.execute(
        select(DataAppTopic).filter_by(data_app_id=data_app_id)).scalars().all()

    for data_app_topic in data_app_topics:
        topic = data_app_topic.topic

        gatt_topic = session.scalar(select(GattTopic).filter_by(topic=topic))

        adv_topic = session.scalar(select(AdvTopic).filter_by(topic=topic))

        if gatt_topic is None and adv_topic is None:
            return jsonify({"status": "FAILURE"}), HTTPStatus.BAD_REQUEST

        if gatt_topic is not None:
            for device in gatt_topic.devices:
                gatt_topic.devices.remove(device)

            session.delete(gatt_topic)

            session.commit()

        if adv_topic is not None:
            for device in adv_topic.devices:
                adv_topic.devices.remove(device)

            session.delete(adv_topic)

            session.commit()

        if adv_topic is not None and adv_topic.onboarded is False:
            if len(adv_topic.filters) > 0:
                session.query(AdvFilter).filter_by(topic=topic).delete()

            session.delete(adv_topic)
            session.commit()

    session.query(DataAppTopic).filter_by(dataAppID=data_app_id).delete()
    session.commit()

    return jsonify({"status": "SUCCESS"}), HTTPStatus.OK


@control_app.route('/registration/topic/data-app/<data_app_id>', methods=['GET'])
@authenticate_user
def get_topics_by_data_app(data_app_id: str):
    """ Fetch registered topics information """
    data_app_topics = session.execute(
        select(DataAppTopic).filter_by(data_app_id=data_app_id)).scalars().all()

    topics = []
    for data_app_topic in data_app_topics:
        topics.append({"topic": data_app_topic.topic})

    return jsonify({
        "status": "SUCCESS",
        "topics": topics
    }), HTTPStatus.OK


@control_app.route('/registration/topic/id/<device_id>', methods=['GET'])
@authenticate_user
def get_topics_by_device_id(device_id: str):
    """ Fetch registered topics information """
    device = session.scalar(select(BleDevice).filter_by(id=device_id))

    if device is None:
        return jsonify({"status": "FAILURE"}), HTTPStatus.BAD_REQUEST

    gatt_topics = session.execute(
        select(GattTopic).filter(GattTopic.devices.contains(device))).scalars().all()

    adv_topics = session.execute(
        select(AdvTopic).filter(AdvTopic.devices.contains(device))).scalars().all()

    topics = []
    for gatt_topic in gatt_topics:
        topics.append({"topic": gatt_topic.topic})

    for adv_topic in adv_topics:
        topics.append({"topic": adv_topic.topic})

    return jsonify({
        "status": "SUCCESS",
        "topics": topics
    }), HTTPStatus.OK


@control_app.route('/registration/topic/id/<device_id>', methods=['DELETE'])
@authenticate_user
def delete_topics_by_device_id(device_id: str):
    """ Function to unregister topic """
    device = session.scalar(select(BleDevice).filter_by(id=device_id))

    if device is None:
        return jsonify({"status": "FAILURE"}), HTTPStatus.BAD_REQUEST

    gatt_topics = session.execute(
        select(GattTopic).filter(GattTopic.devices.contains(device))).scalars().all()

    adv_topics = session.execute(
        select(AdvTopic).filter(AdvTopic.devices.contains(device))).scalars().all()

    for gatt_topic in gatt_topics:
        for device in gatt_topic.devices:
            gatt_topic.devices.remove(device)

        session.delete(gatt_topic)

        session.commit()

    for adv_topic in adv_topics:
        for device in adv_topic.devices:
            adv_topic.devices.remove(device)

        session.delete(adv_topic)

        session.commit()

    return jsonify({"status": "SUCCESS"}), HTTPStatus.OK


@control_app.route('/bulk', methods=['POST'])
@authenticate_user
def bulk():
    """ Function bulk """
    if not request.json:
        return jsonify({"status": "FAILURE"}), HTTPStatus.BAD_REQUEST

    device_id = request.json.get("id")
    control_app_id = request.json.get("controlApp")

    operations = request.json.get("operations", [])

    responses: list[Any] = []

    for operation in operations:
        path = "/control" + operation["operation"]
        method = "POST"
        data = {
            "id": device_id,
            "controlApp": control_app_id,
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
