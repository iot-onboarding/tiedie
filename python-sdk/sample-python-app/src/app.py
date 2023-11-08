# Copyright (c) 2023, Cisco Systems, Inc. and/or its affiliates.
# All rights reserved.
# See LICENSE file in this distribution.
# SPDX-License-Identifier: Apache-2.0
#
"""

A Flask and Socket.IO-based web application for managing Bluetooth Low
Energy (BLE) devices, enabling connections, data interactions, and
real-time updates.

"""

import sys
import os

import uuid
import logging
from flask import Flask, render_template, request, redirect, jsonify
from flask_socketio import SocketIO, Namespace
from google.protobuf.json_format import MessageToJson

from tiedie.models import ( Device, DataFormat, BleDataParameter,
                            AdvertisementRegistrationOptions,
                            ConnectionRegistrationOptions,
                            DataRegistrationOptions, BleExtension,
                            EndpointAppsExtension )
from configuration import ClientConfig

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

client_config = ClientConfig(app)

onboarding_client = client_config.get_onboarding_client()
endpointApps = client_config.get_endpoint_apps(onboarding_client)
control_client = client_config.get_control_client(
    control_app_endpoint=endpointApps[0])
data_receiver_client = client_config.get_data_receiver_client(
    data_app_endpoint=endpointApps[1])

subscriptionTopics = set()
advertisementTopics = set()

class GattHandler(Namespace):
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


class AdvertisementHandler(Namespace):
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


class ConnectionStatusHandler(Namespace):
    """ Manages WebSocket connections and connection status data streams. """
    def on_connect(self):
        """ function to define what happens on connection """
        data_receiver_client.connect()

    def on_disconnect(self):
        """ function to define what happens on disconnection """
        data_receiver_client.disconnect()

    def on_subscribe(self, message):
        """ function to define what happens on subsription """
        def callback(dataSubscription):
            try:
                print("subscription: ", dataSubscription)
                payload = MessageToJson(dataSubscription)

                self.emit('data', {'data': payload})
            except Exception as e:
                print(e)

        print("message: ", message)
        data_receiver_client.subscribe(message, callback)

socketio.on_namespace(ConnectionStatusHandler('/connectionstatus'))


@app.route("/")
def index():
    """ Renders the index page for the web application. """
    return render_template("index.html")


@app.route("/devices")
def get_all_devices():
    """ Displays a list of all IoT devices. """
    response = onboarding_client.getDevices()

    devices = response
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
    admin_state = True if content['adminState'] == 'on' else False
    is_random = True if content['isRandom'] == 'on' else False
    version_support = content['versionSupport'].split(',')
    device = Device(content['deviceDisplayName'], admin_state,
                    BleExtension(
                        content['deviceMacAddress'],
                        version_support,
                        is_random,
                        int(content['passKey'])),
                    endpoint_apps_extension=EndpointAppsExtension(endpointApps))

    response = onboarding_client.createDevice(device)

    if response.status_code != 201:
        return render_template("error.html", error="Failed to create device")

    print("body: ", response.body)

    topic = "data-app/" + response.body['id'] + "/connection"
    dataAppResponse = control_client.register_data_app(
        app.config['DATA_APP_ID'], topic)

    if dataAppResponse.http_status_code != 200:
        return render_template("error.html",
                               error=dataAppResponse.body['message'])

    control_client.register_topic(
        topic,
        ConnectionRegistrationOptions(
            devices=[],
            dataFormat=DataFormat.JSON
        )
    )

    return redirect("/devices")


@app.route("/devices/<id>")
def get_device(id):
    """ function to get get device """
    response = onboarding_client.getDevice(id)

    if response.status_code != 200:
        return render_template("error.html", error="Failed to get device")

    device = response.body

    tiedie_response = control_client.discover(device)
    parameters = None

    if tiedie_response.http_status_code == 200:
        parameters = [
            p for p in tiedie_response.body if isinstance(p, BleDataParameter)
        ]

    device = Device.create(device)

    return render_template(
        "device.html", device=device, parameters=parameters,
    )


@app.route("/devices/<id>/connect", methods=["POST"])
def connect_device(id):
    """ function to connect to a device """
    services = []
    service_uuids = request.form.get('serviceUUIDs')

    if service_uuids:
        services = [uuid.strip() for uuid in service_uuids.split(",")]

    response = onboarding_client.getDevice(id)

    if response.status_code != 200:
        return render_template("error.html", error="Failed to get device")

    device = response.body

    tiedie_response = control_client.connect(
        device, services=services)

    if tiedie_response.http_status_code != 200:
        return render_template("error.html",
                               error="Failed to connect to device")

    return redirect(f"/devices/{id}")


@app.route("/devices/<id>/disconnect", methods=["POST"])
def disconnect_device(id):
    """ function to disconnect a connected device """
    response = onboarding_client.getDevice(id)

    if response.status_code != 200:
        return render_template("error.html", error="Failed to get device")

    device = response.body

    tiedie_response = control_client.disconnect(device)

    if tiedie_response.http_status_code != 200:
        return render_template("error.html")

    return redirect(f"/devices/{id}")


@app.route("/devices/<id>/delete", methods=["POST"])
def delete_device(id):
    """ function to delete device filter """
    response = onboarding_client.deleteDevice(id)

    if response.status_code != 204:
        return render_template("error.html")

    return redirect("/devices")


@app.route('/devices/<string:id>/advertisements', methods=['POST'])
def subscribe_advertisements(id):
    """ function to subscribe to device advertisements """
    response = onboarding_client.getDevice(id)

    device = response.body['id']

    topic = f'data-app/{device}/advertisements/{uuid.uuid4()}'

    device = Device.create(response.body)

    control_client.register_topic(topic,
                                  AdvertisementRegistrationOptions(
                                      devices=[device],
                                      dataFormat=DataFormat.JSON,
                                      advertisementFilterType=None,
                                      advertisementFilters=None
                                  ))
    advertisementTopics.add(topic)
    print("add topic: ", topic)
    return render_template("advertisement.html", topic=topic)


@app.route('/unsubscribe', methods=['POST'])
def unsubscribe():
    """ Unsubscribes from a data stream topic. """
    topic = request.form.get('topic')
    control_client.unregister_topic(topic, [topic.split('/')[1]])
    print("remove topic: ", topic)
    try:
        subscriptionTopics.remove(topic)
    except KeyError:
        pass

    return redirect('/devices')


@app.route("/devices/<id>/svc/<svcUUID>/char/<charUUID>/read",
           methods=["POST"])
def readCharacteristic(id, svcUUID, charUUID):
    parameter = BleDataParameter(id, svcUUID, charUUID)
    response = control_client.read(parameter)
    return response.body.__dict__()
    """ Reads a GATT characteristic of an IoT device. """


@app.route("/devices/<id>/svc/<svcUUID>/char/<charUUID>/write",
           methods=["POST"])
def writeCharacteristic(id, svcUUID, charUUID):
    parameter = BleDataParameter(id, svcUUID, charUUID)
    """ Writes a GATT characteristic of an IoT device. """

    value = request.json["value"]
    print("Writing the paramerter: ")
    print("value: ", value)
    response = control_client.write(parameter, value)

    return jsonify({'value': value})


@app.route('/devices/<string:id>/svc/<string:svcUUID>/char/<string:charUUID>/subscribe',
           methods=['POST'])
def subscribe_characteristic(id: str, svcUUID: str, charUUID: str):
    """ Subscribes to a GATT characteristic of an IoT device. """

    parameter = BleDataParameter(id, svcUUID, charUUID)

    topic = f"data-app/{id}/{svcUUID}/{charUUID}"

    data_app_response = control_client.register_data_app(
        app.config['DATA_APP_ID'], topic)

    if data_app_response.http_status_code != 200:
        return {"error": data_app_response.content}, data_app_response.http_status_code

    topic_response = control_client.register_topic(topic,
                                                   DataRegistrationOptions(
                                                       devices=None,
                                                       dataFormat=DataFormat.JSON,
                                                       dataParameter=parameter)
                                                   )

    if topic_response.http_status_code != 200:
        return {"error": topic_response.body}, topic_response.http_status_code

    subscribe = control_client.subscribe(topic, parameter)

    if subscribe.http_status_code != 200:
        return {"error": subscribe.body}, subscribe.http_status_code
    print("add topic: ", topic)
    subscriptionTopics.add(topic)

    return jsonify({'topic': topic})


@app.route('/advertisements', methods=['POST'])
def subscribe_advertisement():
    """ FUNCTION TO subscribe TO advertisements"""
    request_data = request.json
    print(request_data)

    topic = "data-app/advertisements/" + request_data.get("topic")

    # Register data app
    data_app_response = control_client.register_data_app(
        app.config['DATA_APP_ID'], topic)

    if data_app_response.http_status_code != 200:
        return jsonify({'error': data_app_response.http_message})

    # Register topic
    topic_response = control_client.register_topic(
        topic,
        AdvertisementRegistrationOptions(
            devices=None,
            dataFormat=DataFormat.JSON,
            advertisementFilterType=request_data['filterType'],
            advertisementFilters=request_data['filters']
        )
    )

    if topic_response.http_status_code != 200:
        return jsonify({'error': topic_response.http_message})

    advertisementTopics.add(topic)

    return jsonify({'topic': topic})


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=3000, debug=True)
