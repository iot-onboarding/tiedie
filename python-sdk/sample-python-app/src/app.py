#
# Copyright (c) 2023, Cisco Systems, Inc. and/or its affiliates.
# All rights reserved.
# See accompanying LICENSE file in this distribution
#

import uuid
import os
import logging
from flask import Flask, render_template, request, redirect, jsonify
from flask_socketio import SocketIO, Namespace
from google.protobuf.json_format import MessageToJson

from configuration import ClientConfig 
from tiedie_pylib.models import Device, BleDataParameter, AdvertisementRegistrationOptions, DataRegistrationOptions, BleExtension, EndpointAppsExtension, RegisterDataFormat, ConnectionRegistrationOptions

app = Flask(__name__)
socketio = SocketIO(app, websocket=True, cors_allowed_origins="*")

logger = logging.getLogger('socketio')
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler())

if os.environ.get("DOCKER_BUILD"):
    app.config.from_pyfile("/config/config.ini")
else:
    app.config.from_pyfile("config.ini")

client_config = ClientConfig(app)

onboarding_client = client_config.get_onboarding_client()

data_receiver_client = client_config.get_data_receiver_client(app.config.get('DATA_APP_TOKEN'))
control_client = client_config.get_control_client(app.config.get('CONTROL_APP_TOKEN'))


subscriptionTopics = set()
advertisementTopics = set()   

class GattHandler(Namespace):
    def on_connect(self):
        data_receiver_client.connect()
    
    def on_disconnect(self):
        data_receiver_client.disconnect()
        
    def on_subscribe(self, topic):
        def callback(data_subscription):
            try:
                
                payload = MessageToJson(data_subscription)
                self.emit("data", {'data': payload})
            except Exception as e:
                print(e)
        
        data_receiver_client.subscribe(topic, callback)

    def on_unsubscribe(self, topic):
        data_receiver_client.unsubscribe(topic)
    
    def on_error(self, error):
        print(error)

socketio.on_namespace(GattHandler('/subscription'))

class AdvertisementHandler(Namespace):
    def on_connect(self, environ):
        data_receiver_client.connect()
        
    def on_disconnect(self):
        data_receiver_client.disconnect()
        
    def on_subscribe(self, topic):
        def callback(data_subscription):
            payload = MessageToJson(data_subscription)

            self.emit('data', {'data': payload})
        
        data_receiver_client.subscribe(topic, callback)

    def on_unsubscribe(self):
        data_receiver_client.unsubscribe('advertisements')
        
    def on_error(self, error):
        print(error)

socketio.on_namespace(AdvertisementHandler('/advertisements'))

class ConnectionStatusHandler(Namespace):
    def on_connect(self):
        data_receiver_client.connect()
        
    def on_disconnect(self):
        data_receiver_client.disconnect()

    def on_subscribe(self, message):
        
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
    return render_template("devices.html")


@app.route("/devices")
def get_all_devices():
    return render_template("devices.html")


@app.route("/subscriptions")
def get_subscriptions():
    return render_template("subscriptions.html", subscription_topics=subscriptionTopics, advertisement_topics=advertisementTopics)


@app.route("/subscription",  methods=["GET"])
def get_subscription():
    topic = request.args.get("topic")

    return render_template("subscription.html", topic=topic)


@app.route("/advertisement",  methods=["GET"])
def get_advertisement():
    topic = request.args.get("topic")
    return render_template("advertisement.html", topic=topic)


@app.route("/devices/add", methods=["GET", "POST"])
def add_device():
    if request.method == "GET":
        return render_template('device_add.html')

    content = request.form

    admin_state = True if content.get('adminState', 'off') == 'on' else False
    is_random = True if content.get('isRandom', 'off') == 'on' else False
    version_support = content.getlist('versionSupport')
    device = Device(content['deviceDisplayName'], 
                    admin_state,
                    BleExtension(content['deviceMacAddress'], 
                                version_support,
                                is_random),
                    endpointAppsExtension=EndpointAppsExtension(app.config['ONBOARDING_APP_ID'], [app.config['CONTROL_APP_ID']], [app.config['DATA_APP_ID']]))

    response = onboarding_client.createDevice(device)

    if response.status_code != 200:
        return render_template("error.html", error="Failed to create device")

    id = response.body['id']
    topic = "data-app/" + response.body['id'] + "/connection"
    dataAppResponse = control_client.register_data_app([app.config['DATA_APP_ID']], topic)

    control_client.register_topic(
        topic, 
        ConnectionRegistrationOptions(
            dataformat=RegisterDataFormat.DEFAULT,
            deviceID=id,
        )
    )

    if dataAppResponse.httpStatusCode != 200:
        return render_template("error.html", error=dataAppResponse.body['message'])

    return redirect(f"/devices/{id}")


@app.route("/devices/<id>")
def get_device(id):
    response = onboarding_client.getDevice(id, app.config['ONBOARDING_APP_ID'])

    if response.status_code != 200:
        return render_template("error.html", error=response.httpMessage)

    device = response.body

    tiedie_response = control_client.discover(device, services=["1800", "1805"])
    parameters = None

    if tiedie_response.httpStatusCode == 200:
        parameters = [
            p for p in tiedie_response.services if isinstance(p, BleDataParameter)
        ]
    print("parameters: ", parameters)
    device = Device.create(device)

    return render_template(
        "device.html", device=device, parameters=parameters
    )


@app.route("/devices/<id>/connect", methods=["POST"])
def connect_device(id):
    services = []
    service_uuids = request.form.get('serviceUUIDs')

    if service_uuids:
        services = [uuid.strip() for uuid in service_uuids.split(",")]

    response = onboarding_client.getDevice(id, app.config['ONBOARDING_APP_ID'])

    if response.status_code != 200:
        return render_template("error.html", error="Failed to get device")

    device = response.body

    tiedie_response = control_client.connect(device, services=services)

    if tiedie_response.httpStatusCode != 200:
        return render_template("error.html", error="Failed to connect to device")

    return redirect(f"/devices/{id}")


@app.route("/devices/<id>/disconnect", methods=["POST"])
def disconnect_device(id):
    response = onboarding_client.getDevice(id, app.config['ONBOARDING_APP_ID'])

    if response.status_code != 200:
        return render_template("error.html", error="Failed to get device")

    device = response.body

    tiedie_response = control_client.disconnect(device)

    if tiedie_response.httpStatusCode != 200:
        return render_template("error.html")

    return redirect(f"/devices/{id}")


@app.route("/devices/<id>/delete", methods=["POST"])
def delete_device(id):
    response = onboarding_client.deleteDevice(id, app.config['ONBOARDING_APP_ID'])

    if response.status_code != 200 and response.status_code != 204:
        return render_template("error.html")

    return redirect("/devices")


@app.route('/devices/<string:id>/advertisements', methods=['POST'])
def subscribe_advertisements(id):
    response = onboarding_client.getDevice(id, app.config['ONBOARDING_APP_ID'])

    device = response.body['id']

    topic = f'data-app/{device}/advertisements'

    data_app_response = control_client.register_data_app([app.config['DATA_APP_ID']], topic)

    if data_app_response.httpStatusCode != 200:
        return {"error": data_app_response.httpMessage}, data_app_response.httpStatusCode

    device = Device.create(response.body)

    control_client.register_topic(topic,
                                  AdvertisementRegistrationOptions(
                                deviceID = device.deviceID,
                                dataformat=RegisterDataFormat.DEFAULT,
                                filterType=None,
                                filters=None
        ))
    advertisementTopics.add(topic)

    return render_template("advertisement.html", topic=topic)


@app.route('/unsubscribe', methods=['POST'])
def unsubscribe():
    topic = request.form.get('topic')

    control_client.unregister_topic(topic, topic.split('/')[1])
    try:
        advertisementTopics.remove(topic)
        
    except KeyError:
        subscriptionTopics.remove(topic)
        data = topic.split('/')
        if len(data) == 4:
            parameter = BleDataParameter(data[1], data[2], data[3])

            subscribe = control_client.unsubscribe(topic, parameter)

            if subscribe.httpStatusCode != 200:
                return {"error": subscribe.body}, subscribe.httpStatusCode


    return redirect('/devices')


@app.route("/devices/<id>/svc/<svcUUID>/char/<charUUID>/read", methods=["POST"])
def readCharacteristic(id, svcUUID, charUUID):
    parameter = BleDataParameter(id, svcUUID, charUUID)
    response = control_client.read(parameter)

    if response["status"] != "SUCCESS":
        return render_template("error.html", error=response["reason"])
    
    return response


@app.route("/devices/<id>/svc/<svcUUID>/char/<charUUID>/write", methods=["POST"])
def writeCharacteristic(id, svcUUID, charUUID):
    parameter = BleDataParameter(id, svcUUID, charUUID)
    
    value = request.json["value"]
    response = control_client.write(parameter, value)

    if response["status"] != "SUCCESS":
        return jsonify({'error': response["reason"]}), 400

    return jsonify({'value': value})


@app.route('/devices/<string:id>/svc/<string:svcUUID>/char/<string:charUUID>/subscribe', methods=['POST'])
def subscribe_characteristic(id: str, svcUUID: str, charUUID: str):

    parameter = BleDataParameter(id, svcUUID, charUUID)

    topic = f"data-app/{id}/{svcUUID}/{charUUID}"

    data_app_response = control_client.register_data_app([app.config['DATA_APP_ID']], topic)

    if data_app_response.httpStatusCode != 200:
        return {"error": data_app_response.httpMessage}, data_app_response.httpStatusCode

    topic_response = control_client.register_topic(topic, 
                                                   DataRegistrationOptions(
                                                        parameter,
                                                        RegisterDataFormat.DEFAULT)
                                                )

    if topic_response.httpStatusCode != 200:
        return {"error": topic_response.body}, topic_response.httpStatusCode
    
    subscribe = control_client.subscribe(topic, parameter)

    if subscribe.httpStatusCode != 200:
        return {"error": subscribe.body}, subscribe.httpStatusCode

    subscriptionTopics.add(topic)

    return jsonify({'topic': topic})


@app.route('/advertisements', methods=['POST'])
def subscribe_advertisement():
    request_data = request.json

    topic = "data-app/advertisements/" + request_data.get("topic")

    # Register data app
    data_app_response = control_client.register_data_app([app.config['DATA_APP_ID']], topic)

    if data_app_response.httpStatusCode != 200:
        return jsonify({'error': data_app_response.httpMessage})
    
    # Register topic
    topic_response = control_client.register_topic(
        topic, 
        AdvertisementRegistrationOptions(
            dataformat=RegisterDataFormat.DEFAULT,
        )
    )

    if topic_response.httpStatusCode != 200:
        return jsonify({'error': topic_response.httpMessage})

    advertisementTopics.add(topic)

    return jsonify({'topic': topic})


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=3000)
