# Copyright (c) 2023, Cisco Systems, Inc. and/or its affiliates.
# All rights reserved.
# See LICENSE file in this distribution.
# SPDX-License-Identifier: Apache-2.0

"""

A Flask and Socket.IO-based web application for managing Bluetooth Low
Energy (BLE) devices, enabling connections, data interactions, and
real-time updates.

"""

import base64
import json
import sys
import os

import logging
from urllib.parse import quote, unquote
from flask import Flask, render_template, request, redirect
from flask_socketio import SocketIO, namespace
from requests_oauth2client import OAuth2AuthorizationCodeAuth
from tiedie.models import (Device, BleDataParameter,
                           BleExtension,
                           DataAppRegistration,
                           EndpointAppsExtension)
from tiedie.models.ble import BleConnectRequest, BleService
from tiedie.models.requests import SdfModel
from tiedie.models.responses import Event, MqttBrokerConfig
from tiedie.models.scim import Application, NullPairing, PairingJustWorks
import configuration


sys.path.append(os.path.dirname(os.path.dirname(os.getcwd())))

app = Flask(__name__)
socketio = SocketIO(app, websocket=True, cors_allowed_origins="*")

app.jinja_env.filters['quote'] = lambda s: quote(s, safe='')

logger = logging.getLogger('socketio')
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler())

tiedie_logger = logging.getLogger('tiedie')
tiedie_logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter(
    '[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s'))
tiedie_logger.addHandler(handler)

if os.environ.get("DOCKER_BUILD"):
    app.config.from_pyfile("/config/config.ini")
else:
    app.config.from_pyfile("../config/config.ini")

client_config = configuration.ClientConfig(app)

az_request = None
onboarding_client = None
control_client = None
data_receiver_client = None

def init_clients():
    """ Initializes the clients for onboarding, control, and data receiver. """
    global onboarding_client, control_client, data_receiver_client, endpoint_apps, data_endpoint_app

    if onboarding_client is None:
        print("Initializing clients...")
        onboarding_client = client_config.get_onboarding_client()
        endpoint_apps = client_config.get_endpoint_apps(onboarding_client)

        data_endpoint_app = endpoint_apps[1]
        control_client = client_config.get_control_client(
            control_app_endpoint=endpoint_apps[0])
        data_receiver_client = client_config.get_data_receiver_client(
            data_app_endpoint=data_endpoint_app)

@app.before_request
def redirect_to_oauth():
    """ Redirects to OAuth2 authorization endpoint if client ID is provided. """
    global az_request
    if client_config.oauth_client_id is not None and az_request is None and not request.path.startswith("/oauth"):
        return redirect("/oauth2/authorize")
    if not request.path.startswith("/oauth"):
        init_clients()


@app.route("/oauth2/authorize", methods=["GET", "POST"])
def oauth2_authorize():
    """ Redirects to OAuth2 authorization endpoint. """
    global az_request
    if request.method == "GET":
        return render_template("oauth2_authorize.html")
    if client_config.oauth2client is not None:
        az_request = client_config.oauth2client.authorization_request(scope=client_config.oauth_scopes)
        return redirect(az_request.uri)
    else:
        return render_template("error.html", error="OAuth2 client not configured.")


@app.route("/oauth_callback")
def oauth_callback():
    """ Handles the OAuth2 callback and retrieves the access token. """
    global az_request
    if client_config.oauth2client is None:
        return render_template("error.html", error="OAuth2 client not configured.")

    az_response = az_request.validate_callback(request.url)
    if az_response.code is None:
        az_request = None
    client_config.oauth_authenticator.session_auth = OAuth2AuthorizationCodeAuth(
        client_config.oauth2client,
        code=az_response,
    )
    init_clients()
    return redirect("/devices")


def update_data_app(event: str, enable: bool):
    """ function to update data app """
    response = control_client.get_data_app(data_endpoint_app.application_id)
    if response.http and response.http.status_code != 200 or response.body is None:
        if client_config.data_app_mqtt_type == "broker":
            # read DATA_APP_CA_CERT_PATH from config
            ca_cert = None
            ca_cert_path = client_config.data_app_ca_cert_path
            if ca_cert_path is not None:
                with open(ca_cert_path, 'r', encoding='utf-8') as ca_cert_file:
                    ca_cert = ca_cert_file.read()
            mqtt_broker = MqttBrokerConfig(
                uri=f"{client_config.data_app_host}:{client_config.data_app_port}",
                username=client_config.data_app_username,
                password=client_config.data_app_password,
                broker_ca_cert=ca_cert,
            )
            # register data app
            response = control_client.create_data_app(
                data_endpoint_app.application_id,
                DataAppRegistration(
                    events=[Event(event=event)],
                    mqtt_client=None,
                    mqtt_broker=mqtt_broker,
                ))
        else:
            # register data app
            response = control_client.create_data_app(
                data_endpoint_app.application_id,
                DataAppRegistration(
                    events=[Event(event=event)],
                    mqtt_client={},
                    mqtt_broker=None,
                ))
    else:
        data_app = response.body
        # update data app
        # append new events to the existing events
        events = data_app.events
        if enable:
            if event not in [e.event for e in events]:
                events.append(Event(event=event))
        else:
            for e in events:
                if e.event == event:
                    events.remove(e)
                    break

        if len(events) == 0:
            # remove data app
            response = control_client.delete_data_app(
                data_endpoint_app.application_id)
            return

        response = control_client.update_data_app(
            data_endpoint_app.application_id,
            DataAppRegistration(
                events=events,
                mqtt_client=data_app.mqtt_client,
                mqtt_broker=data_app.mqtt_broker,
            ))


class SubscriptionHandler(namespace.Namespace):
    """
    WebSocket handler for GATT (Bluetooth) connections and data
    subscriptions.
    """

    def on_connect(self, *_):
        """ function to define what happens on connection """
        data_receiver_client.connect()

    def on_disconnect(self):
        """ function to define what happens on disconnection """
        data_receiver_client.disconnect()

    def on_subscribe(self, event):
        """ function to define what happens on subscription """
        def callback(data_subscription: list[dict]):
            try:
                for data in data_subscription:
                    if data["data"] is not None:
                        data["data"] = base64.b64encode(
                            data["data"]).decode("utf-8")
                payload = json.dumps(data_subscription)
                self.emit("data", {'data': payload})
            except Exception as e:
                print(e)

        print(event)
        topic = quote(event, safe='')
        data_receiver_client.subscribe(topic, callback)

    def on_unsubscribe(self, event):
        """ function to define what happens on unsubscription """
        topic = quote(event, safe='')
        data_receiver_client.unsubscribe(topic)

    def on_error(self, error):
        """ function to define what happens on error """
        print(error)


socketio.on_namespace(SubscriptionHandler('/subscription'))


@app.route("/")
def index():
    """ Renders the index page for the web application. """
    return redirect("/devices")


@app.route("/devices")
def get_all_devices():
    """ Displays a list of all IoT devices. """
    response = onboarding_client.get_devices()

    if response.status_code != 200 or response.body is None:
        return render_template("error.html", error="Failed to get devices")

    devices = response.body.resources
    return render_template("devices.html", devices=devices)


@app.route("/data_app")
def get_subscriptions():
    """ Displays subscription topics and BLE advertisement topics. """
    topic = quote(f'data-app/{data_endpoint_app.application_id}/#')
    # redirect to get_subscription with the topic
    return redirect(f"/subscription?event={topic}")

@app.route("/subscription",  methods=["GET"])
def get_subscription():
    """ Displays details of a specific subscription topic. """
    event = request.args.get("event")

    return render_template("subscription.html", event=event)


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
            null_pairing=NullPairing() if pairing_method == 'null' else None,
            pairing_just_works=PairingJustWorks() if pairing_method == 'justWorks' else None,
        ),
        endpoint_apps_extension=EndpointAppsExtension(applications=[
            Application(value=endpoint_app.application_id) for endpoint_app in endpoint_apps
        ])
    )

    response = onboarding_client.create_device(device)

    if response.status_code != 201 or response.body is None or response.body.device_id is None:
        return render_template("error.html", error="Failed to create device")

    return redirect("/devices")


@app.route("/devices/<device_id>/update", methods=["GET", "POST"])
def update_device(device_id):
    """ Update device in the app """
    response = onboarding_client.get_device(device_id)

    if response.status_code != 200 or response.body is None:
        return render_template("error.html", error="Failed to get device")

    device = response.body

    if request.method == "GET":
        return render_template("device_update.html", device=device)

    content = request.form.to_dict()
    print(request.form)

    active = content.get('active', 'off') == 'on'
    is_random = content.get('isRandom', 'off') == 'on'
    version_support = request.form.getlist('versionSupport')

    pairing_method = content.get('pairingMethod')
    mobility = content.get('mobility', 'off') == 'on'

    device = Device(
        device_id=device_id,
        display_name=content['displayName'],
        active=active,
        ble_extension=BleExtension(
            device_mac_address=content['deviceMacAddress'],
            version_support=version_support,
            is_random=is_random,
            mobility=mobility,
            null_pairing=NullPairing() if pairing_method == 'null' else None,
            pairing_just_works=PairingJustWorks() if pairing_method == 'justWorks' else None,
        ),
        endpoint_apps_extension=EndpointAppsExtension(applications=[
            Application(value=endpoint_app.application_id) for endpoint_app in endpoint_apps
        ])
    )

    response = onboarding_client.update_device(device)

    if response.status_code != 201 or response.body is None or response.body.device_id is None:
        return render_template("error.html", error="Failed to create device")

    return redirect(f"/devices/{device_id}")


@app.route("/devices/<device_id>")
def get_device(device_id):
    """ function to get get device """
    response = onboarding_client.get_device(device_id)

    if response.status_code != 200 or response.body is None:
        return render_template("error.html", error="Failed to get device")

    device = response.body

    sdf_models = {}

    response = control_client.get_sdf_models()

    if response.status_code == 200 and response.body is not None and len(response.body.root) > 0:
        print(response.body)
        for sdf_ref_resp in response.body.root:
            response = control_client.get_sdf_model(sdf_ref_resp.sdf_ref)
            if response.status_code == 200 and response.body is not None:
                sdf_models[sdf_ref_resp.sdf_ref] = response.body

    tiedie_response = control_client.get_connection(device)

    parameters = None
    # pass the parameters to the template
    if tiedie_response.http and tiedie_response.http.status_code == 200 and \
            tiedie_response.body is not None:
        parameters = [
            p for p in tiedie_response.body if isinstance(p, BleDataParameter)
        ]

    events = []
    response = control_client.get_all_events(device_id)
    # pass the events to the template
    if response.http and response.http.status_code == 200 and response.body is not None:
        events = [response.event for response in response.body.events]

    return render_template(
        "device.html",
        device=device,
        parameters=parameters,
        sdf_models=sdf_models,
        events=events
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


@app.route("/devices/<device_id>/svc/<service_id>/char/<char_id>/read",
           methods=["POST"])
def read_characteristic(device_id, service_id, char_id):
    """ Reads a GATT characteristic of an IoT device. """
    response = onboarding_client.get_device(device_id)

    if response.status_code != 200 or response.body is None:
        return render_template("error.html", error="Failed to get device")

    device = response.body

    response = control_client.read(device, service_id, char_id)
    return response.body.model_dump_json() if response.body else ""


@app.route("/devices/<device_id>/svc/<service_id>/char/<char_id>/write",
           methods=["POST"])
def write_characteristic(device_id: str, service_id: str, char_id: str):
    """ Writes a GATT characteristic of an IoT device. """
    if request.json is None:
        return ""

    response = onboarding_client.get_device(device_id)

    if response.status_code != 200 or response.body is None:
        return render_template("error.html", error="Failed to get device")

    device = response.body

    value: str = request.json["value"]
    response = control_client.write(device, service_id, char_id, value)

    return response.body.model_dump_json() if response.body else ""


@app.route("/devices/<device_id>/read", methods=["POST"])
def read_property(device_id):
    """ Reads a property of an IoT device. """
    if request.json is None:
        return render_template("error.html", error="Invalid request")

    property_name = request.json["sdfRef"]
    response = control_client.read_property(device_id, property_name)

    return response.body.model_dump_json() if response.body else ""


@app.route("/devices/<device_id>/write", methods=["POST"])
def write_property(device_id):
    """ Writes a property of an IoT device. """
    if request.json is None:
        return render_template("error.html", error="Invalid request")

    property_name = request.json["sdfRef"]
    value = request.json["value"]
    response = control_client.write_property(device_id, property_name, value)

    return response.body.model_dump_json() if response.body else ""


@app.route("/devices/<device_id>/sdf", methods=["POST"])
def register_sdf_model(device_id: str):
    """ Registers a new SDF model for a device. """

    if 'sdfFile' not in request.files:
        return render_template("error.html", error="No file part")

    file = request.files['sdfFile']

    sdf_file = file.stream.read()

    sdf_model = SdfModel.model_validate_json(sdf_file)

    sdf_ref = sdf_model.namespace[sdf_model.default_namespace]

    if sdf_model.sdf_thing is not None and len(sdf_model.sdf_thing) > 0:
        sdf_ref += "#/" + list(sdf_model.sdf_thing.keys())[0]
    elif sdf_model.sdf_object is not None and len(sdf_model.sdf_object) > 0:
        sdf_ref += "#/" + list(sdf_model.sdf_object.keys())[0]

    response = control_client.get_sdf_models()

    # if the response contains the same ref, update else register
    if response.status_code == 200 and response.body is not None and \
            len(response.body.root) > 0 and \
            any(sdf_ref_resp.sdf_ref == sdf_ref for sdf_ref_resp in response.body.root):
        print(response.body)
        encoded_ref = quote(sdf_ref, safe='')
        response = control_client.update_sdf_model(encoded_ref, sdf_model)
    else:
        response = control_client.register_sdf_model(sdf_model)

    if response.http is not None and response.http.status_code != 200:
        return render_template("error.html", error="Failed to register SDF model")

    return redirect(f"/devices/{device_id}")


@app.route("/devices/<device_id>/deleteSdf/<sdf_ref>", methods=["POST"])
def delete_sdf_model(device_id: str, sdf_ref: str):
    """ Deletes an SDF model from a device. """
    unquoted_sdf_ref = unquote(sdf_ref)

    response = control_client.unregister_sdf_model(unquoted_sdf_ref)

    if response.http is not None and response.http.status_code != 200:
        return render_template("error.html", error="Failed to delete SDF model")

    return redirect(f"/devices/{device_id}")


@app.route("/devices/<device_id>/event", methods=["POST"])
def register_event(device_id: str):
    """ Registers a new event for a device. """
    if request.json is None:
        return render_template("error.html", error="Invalid request")

    sdf_ref = request.json["sdfRef"]
    enable = request.json["enable"]

    if enable:
        update_data_app(sdf_ref, enable)

    if enable:
        response = control_client.enable_event(device_id, sdf_ref)
    else:
        response = control_client.disable_event(device_id, sdf_ref)

    # remove event from data app if the event was disabled successfully
    if response.http and response.http.status_code == 200 and not enable:
        update_data_app(sdf_ref, enable)

    return response.body.model_dump_json() if response.body else ""


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=3000, debug=True)
