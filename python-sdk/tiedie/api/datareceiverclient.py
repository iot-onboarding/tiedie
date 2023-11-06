#!python
# Copyright (c) 2023, Cisco Systems, Inc. and/or its affiliates.
# All rights reserved.
# See LICENSE file in this distribution.
# SPDX-License-Identifier: Apache-2.0
"""

The mmodule defines a Python client using Paho MQTT for receiving and 
handling data from an MQTT broker, particularly for IoT applications.

"""

from typing import Callable, Optional
import paho.mqtt.client as mqtt
from .auth import Authenticator
from .proto import data_app_pb2


class DataReceiverClient:
    """ class DataReceiverClient """
    def __init__(self, 
                 host: str,
                   authenticator: Authenticator,
                     port: int = 8883, 
                     disable_tls: bool = False):
        self.host = host
        self.port = port
        self.authenticator = authenticator
        self.mqtt_client = mqtt.Client(client_id=authenticator.get_client_id(), clean_session=True)
        if not disable_tls:
            self.authenticator.set_auth_options_mqtt(self.mqtt_client)
        self.mqtt_client.on_connect = self.on_connect
        self.mqtt_client.on_disconnect = self.on_disconnect
        self.mqtt_client.on_message = self.on_message
        self.connected = False


    def connect(self):
        """ function to define what happens on connection """
        self.mqtt_client.connect(self.host, self.port, 60)
        self.mqtt_client.loop_start()


    def disconnect(self):
        """ function to define what happens on disconnection """
        self.mqtt_client.disconnect()
        self.mqtt_client.loop_stop()


    def subscribe(self,topic:str,
                  callback:Callable[[Optional[data_app_pb2.DataSubscription]],
                                    None]):
        """ function to define what happens on subscription """
        def on_message(_client, _userdata, msg):
            payload = msg.payload
            data_subscription = data_app_pb2.DataSubscription()
            data_subscription.ParseFromString(payload)
            callback(data_subscription)

        self.mqtt_client.subscribe(topic, qos=0)
        self.mqtt_client.on_message = on_message

    def unsubscribe(self, topic: str):
        """ function to define what happens on unsubscription """
        self.mqtt_client.unsubscribe(topic)

    def on_message(self, message):
        """ function to define what happens on message """
        print("Received message: " + str(message.payload))

    def on_connect(self, _client, _userdata, _flags, rc):
        """ function to define what happens on connection """
        if rc == 0:
            print("Connected to broker")
            self.connected = True
        else:
            print("Connection failed with error code " + str(rc))

    def on_disconnect(self, _client, _userdata, _rc):
        """ function to define what happens on disconnection """
        print("Disconnected from broker")
        self.connected = False
