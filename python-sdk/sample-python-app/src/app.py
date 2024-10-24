# Copyright (c) 2023, Cisco Systems, Inc. and/or its affiliates.
# All rights reserved.
# See LICENSE file in this distribution.
# SPDX-License-Identifier: Apache-2.0

"""

A Flask and Socket.IO-based web application for managing Bluetooth Low
Energy (BLE) devices, enabling connections, data interactions, and
real-time updates.

"""

import sys
import os

import logging
from flask import Flask, render_template, request, redirect, jsonify
from flask_socketio import SocketIO, namespace
from google.protobuf.json_format import MessageToJson
from tiedie.models import (Device, DataFormat, BleDataParameter,
                           AdvertisementRegistrationOptions,
                           ConnectionRegistrationOptions,
                           DataRegistrationOptions, BleExtension,
                           EndpointAppsExtension)
from tiedie.models.ble import BleConnectRequest, BleService
from tiedie.models.scim import Application, NullPairing, PairingJustWorks
import configuration


sys.path.append(os.path.dirname(os.path.dirname(os.getcwd())))

app = Flask(__name__)
socketio = SocketIO(app, websocket=True, cors_allowed_origins="*")

logger = logging.getLogger('socketio')
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler())

if os.environ.get("DOCKER_BUILD"):
    app.config.from_pyfile("/config/config.ini")
else:
    app.config.from_pyfile("../config/config.ini")

client_config = configuration.ClientConfig(app)

onboarding_client = client_config.get_onboarding_client()
endpoint_apps = client_config.get_endpoint_apps(onboarding_client)
control_client = client_config.get_control_client(
    control_app_endpoint=endpoint_apps[0])
data_receiver_client = client_config.get_data_receiver_client(
    data_app_endpoint=endpoint_apps[1])

subscriptionTopics = set()
advertisementTopics = set()


class GattHandler(namespace.Namespace):
    """
    WebSocket handler for GATT (Bluetooth) connections and data
    subscriptions.
    """

    def on_connect(self):
        """ function to define what happens on connection """
        data_receiver_client.connect()

    def on_disconnect(self):
        """ function to define what happens on disconnection """
        data_receiver_client.disconnect()

    def on_subscribe(self, topic):
        """ function to define what happens on subscription """
        def callback(data_subscription):
            try:
                payload = MessageToJson(data_subscription)
                self.emit("data", {'data': payload})
            except Exception as e:
                print(e)

        data_receiver_client.subscribe(topic, callback)

    def on_unsubscribe(self, topic):
        """ function to define what happens on unsubscription """
        data_receiver_client.unsubscribe(topic)

    def on_error(self, error):
        """ function to define what happens on error """
        print(error)


socketio.on_namespace(GattHandler('/subscription'))


class AdvertisementHandler(namespace.Namespace):
    """ Handles BLE advertisement subscriptions and data stream management. """

    def on_connect(self):
        """ function to define what happens on connection """
        data_receiver_client.connect()

    def on_disconnect(self):
        """ function to define what happens on discpnnection """
        data_receiver_client.disconnect()

    def on_subscribe(self, topic):
        """ function to define what happens on subscription """
        def callback(data_subscription):
            print("subscription: ", data_subscription)

            payload = MessageToJson(data_subscription)

            self.emit('data', {'data': payload})

        data_receiver_client.subscribe(topic, callback)

    def on_unsubscribe(self, topic):
        """ function to define what happens on unsubscription """
        data_receiver_client.unsubscribe(topic)

    def on_error(self, error):
        """ function to define what happens on error """
        print(error)


socketio.on_namespace(AdvertisementHandler('/advertisements'))


class ConnectionStatusHandler(namespace.Namespace):
    """ Manages WebSocket connections and connection status data streams. """

    def on_connect(self):
        """ function to define what happens on connection """
        data_receiver_client.connect()

    def on_disconnect(self):
        """ function to define what happens on disconnection """
        data_receiver_client.disconnect()

    def on_subscribe(self, message):
        """ function to define what happens on subsription """
        def callback(data_subscription):
            try:
                print("subscription: ", data_subscription)
                payload = MessageToJson(data_subscription)

                self.emit('data', {'data': payload})
            except Exception as e:
                print(e)

        print("message: ", message)
        if len(message) != 0:
            data_receiver_client.subscribe(message, callback)


socketio.on_namespace(ConnectionStatusHandler('/connectionstatus'))


@app.route("/")
def index():
    """ Renders the index page for the web application. """
    return render_template("index.html")


@app.route("/devices")
def get_all_devices():
    """ Displays a list of all IoT devices. """
    response = onboarding_client.get_devices()

    if response.status_code != 200 or response.body is None:
        return render_template("error.html", error="Failed to get devices")

    devices = response.body.resources
    print(devices)
    return render_template("devices.html", devices=devices)


@app.route("/subscriptions")
def get_subscriptions():
    """ Displays subscription topics and BLE advertisement topics. """
    return render_template("subscriptions.html",
                           subscription_topics=subscriptionTopics,
                           advertisement_topics=advertisementTopics)


@app.route("/subscription",  methods=["GET"])
def get_subscription():
    """ Displays details of a specific subscription topic. """
    topic = request.args.get("topic")

    return render_template("subscription.html", topic=topic)


@app.route("/advertisement",  methods=["GET"])
def get_advertisement():
    """ Displays details of a specific BLE advertisement topic. """
    topic = request.args.get("topic")
    return render_template("advertisement.html", topic=topic)


@app.route("/devices/add", methods=["GET", "POST"])
def add_device():
    """ add device in the app """
    if request.method == "GET":
        return render_template('device_add.html')

    content = request.form.to_dict()
    print(content)
    active = content.get('active', 'off') == 'on'
    is_random = content.get('isRandom', 'off') == 'on'
    version_support = content['versionSupport'].split(',')

    pairing_method = content.get('pairingMethod')
    mobility = content.get('mobility', 'off') == 'on'

    device = Device(
        display_name=content['displayName'],
        active=active,
        ble_extension=BleExtension(
            device_mac_address=content['deviceMacAddress'],
            version_support=version_support,
            is_random=is_random,
            mobility=mobility,
            null_pairing= NullPairing() if pairing_method == 'null' else None,
            pairing_just_works= PairingJustWorks() if pairing_method == 'justWorks' else None,
        ),
        endpoint_apps_extension=EndpointAppsExtension(applications=[
            Application(value=endpoint_app.application_id) for endpoint_app in endpoint_apps
        ])
    )

    response = onboarding_client.create_device(device)

    if response.status_code != 201 or response.body is None or response.body.device_id is None:
        return render_template("error.html", error="Failed to create device")

    print("body: ", response.body)

    topic = "data-app/" + response.body.device_id + "/connection"

    control_client.register_event(
        topic,
        response.body,
        ConnectionRegistrationOptions(
            data_format=DataFormat.DEFAULT,
            data_apps=[app.config['DATA_APP_ID']]
        )
    )

    return redirect("/devices")


@app.route("/devices/<device_id>")
def get_device(device_id):
    """ function to get get device """
    response = onboarding_client.get_device(device_id)

    if response.status_code != 200 or response.body is None:
        return render_template("error.html", error="Failed to get device")

    device = response.body

    tiedie_response = control_client.discover(device)
    parameters = None

    if tiedie_response.http and tiedie_response.http.status_code == 200 and tiedie_response.body:
        parameters = [
            p for p in tiedie_response.body if isinstance(p, BleDataParameter)
        ]

    return render_template(
        "device.html", device=device, parameters=parameters,
    )


@app.route("/devices/<device_id>/connect", methods=["POST"])
def connect_device(device_id):
    """ function to connect to a device """
    services = []
    service_uuids = request.form.get('serviceUUIDs')

    if service_uuids:
        services = [uuid.strip() for uuid in service_uuids.split(",")]

    response = onboarding_client.get_device(device_id)

    if response.status_code != 200 or response.body is None:
        return render_template("error.html", error="Failed to get device")

    device = response.body

    tiedie_response = control_client.connect(device,
                                             BleConnectRequest(services=[
                                                 BleService(service_id=service)
                                                 for service in services
                                             ]))

    if tiedie_response.http is None or tiedie_response.http.status_code != 200:
        return render_template("error.html",
                               error="Failed to connect to device")

    return redirect(f"/devices/{device_id}")


@app.route("/devices/<device_id>/disconnect", methods=["POST"])
def disconnect_device(device_id):
    """ function to disconnect a connected device """
    response = onboarding_client.get_device(device_id)

    if response.status_code != 200 or response.body is None:
        return render_template("error.html", error="Failed to get device")

    device = response.body

    tiedie_response = control_client.disconnect(device)

    if tiedie_response.http is None or tiedie_response.http.status_code != 200:
        return render_template("error.html")

    return redirect(f"/devices/{device_id}")


@app.route("/devices/<device_id>/delete", methods=["POST"])
def delete_device(device_id):
    """ function to delete device filter """
    response = onboarding_client.delete_device(device_id)

    if response.status_code != 204:
        return render_template("error.html")

    return redirect("/devices")


@app.route('/devices/<device_id>/advertisements', methods=['POST'])
def subscribe_advertisements(device_id):
    """ function to subscribe to device advertisements """
    response = onboarding_client.get_device(device_id)

    if response.status_code != 200 or response.body is None:
        return render_template("error.html", error="Failed to get device")

    device = response.body

    topic = f'data-app/{device.device_id}/advertisements'

    control_client.register_event(topic,
                                  device,
                                  AdvertisementRegistrationOptions(
                                      data_apps=[app.config['DATA_APP_ID']],
                                      data_format=DataFormat.DEFAULT,
                                  ))
    advertisementTopics.add(topic)
    print("add topic: ", topic)
    return render_template("advertisement.html", topic=topic)


@app.route('/unsubscribe', methods=['POST'])
def unsubscribe():
    """ Unsubscribes from a data stream topic. """
    topic = request.form.get('topic')

    if topic is None:
        return render_template("error.html", error="Invalid topic string")

    control_client.unregister_event(topic)
    print("remove topic: ", topic)
    try:
        subscriptionTopics.remove(topic)
    except KeyError:
        pass

    return redirect('/devices')


@app.route("/devices/<device_id>/svc/<service_id>/char/<char_id>/read",
           methods=["POST"])
def read_characteristic(device_id, service_id, char_id):
    """ Reads a GATT characteristic of an IoT device. """
    response = onboarding_client.get_device(device_id)

    if response.status_code != 200 or response.body is None:
        return render_template("error.html", error="Failed to get device")

    device = response.body

    parameter = BleDataParameter(
        device_id=device_id,
        service_id=service_id,
        characteristic_id=char_id)
    response = control_client.read(device, parameter)
    return response.model_dump_json()


@app.route("/devices/<device_id>/svc/<service_id>/char/<char_id>/write",
           methods=["POST"])
def write_characteristic(device_id, service_id, char_id):
    """ Writes a GATT characteristic of an IoT device. """
    response = onboarding_client.get_device(device_id)

    if response.status_code != 200 or response.body is None:
        return render_template("error.html", error="Failed to get device")

    device = response.body

    parameter = BleDataParameter(
        device_id=device_id,
        service_id=service_id,
        characteristic_id=char_id)

    value = request.json["value"]
    print("Writing the paramerter: ")
    print("value: ", value)
    response = control_client.write(device, parameter, value)

    return response.model_dump_json()


@app.route('/devices/<string:device_id>/svc/<string:service_id>/char/<string:char_id>/subscribe',
           methods=['POST'])
def subscribe_characteristic(device_id: str, service_id: str, char_id: str):
    """ Subscribes to a GATT characteristic of an IoT device. """
    response = onboarding_client.get_device(device_id)

    if response.status_code != 200 or response.body is None:
        return render_template("error.html", error="Failed to get device")

    device = response.body

    parameter = BleDataParameter(
        device_id=device_id,
        service_id=service_id,
        characteristic_id=char_id)

    topic = f"data-app/{device_id}/{service_id}/{char_id}"

    topic_response = control_client.register_event(topic,
                                                   device,
                                                   DataRegistrationOptions(
                                                       data_apps=[
                                                           app.config['DATA_APP_ID']],
                                                       data_format=DataFormat.DEFAULT,
                                                       data_parameter=parameter)
                                                   )

    if topic_response.http and topic_response.http.status_code != 200:
        return {"error": topic_response.body}, topic_response.http.status_code

    subscribe = control_client.subscribe(device, parameter)

    if subscribe.http and subscribe.http.status_code != 200:
        return {"error": subscribe.body}, subscribe.http.status_code
    print("add topic: ", topic)
    subscriptionTopics.add(topic)

    return jsonify({'topic': topic})


@app.route('/advertisements', methods=['POST'])
def subscribe_advertisement():
    """ FUNCTION TO subscribe TO advertisements"""
    request_data = request.json
    print(request_data)

    topic = "data-app/advertisements/" + request_data.get("topic")

    # Register topic
    topic_response = control_client.register_event(
        topic,
        None,
        AdvertisementRegistrationOptions(
            data_format=DataFormat.DEFAULT,
            data_apps=[app.config['DATA_APP_ID']],
            advertisement_filter_type=request_data['filterType'],
            advertisement_filters=request_data['filters']
        )
    )

    if topic_response.http.status_code != 200:
        return jsonify({'error': topic_response.http.status_message})

    advertisementTopics.add(topic)

    return jsonify({'topic': topic})


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=3000, debug=True)
