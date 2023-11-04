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
from .auth import Authenticator
import paho.mqtt.client as mqtt
from .proto import data_app_pb2


class DataReceiverClient:
    """ class DataREcieverClient """
    def __init__(self, baseUrl: str, authenticator: Authenticator, port: int = 8883):
        self.baseUrl = baseUrl
        self.port = port
        self.authenticator = authenticator
        self.mqttClient = mqtt.Client(client_id=authenticator.get_client_id(), clean_session=True)
        self.authenticator.set_ssl_context_mqtt(self.mqttClient)
        self.mqttClient.on_connect = self.on_connect
        self.mqttClient.on_disconnect = self.on_disconnect
        self.mqttClient.on_message = self.on_message
        self.connected = False


    def connect(self):
        """ function to define what happens on connection """
        self.mqttClient.connect(self.baseUrl, self.port, 60)
        self.mqttClient.loop_start()


    def disconnect(self):
        """ function to define what happens on disconnection """
        self.mqttClient.disconnect()
        self.mqttClient.loop_stop()


    def subscribe(self,topic:str,
                  callback:Callable[[Optional[data_app_pb2.DataSubscription]],
                                    None]):
        """ function to define what happens on subscription """
        def on_message(client, userdata, msg):
            payload = msg.payload
            data_subscription = data_app_pb2.DataSubscription()
            data_subscription.ParseFromString(payload)
            callback(data_subscription)

        self.mqttClient.subscribe(topic, qos=0)
        self.mqttClient.on_message = on_message

    def unsubscribe(self, topic: str):
        """ function to define what happens on unsubscription """
        self.mqttClient.unsubscribe(topic)

    def on_message(self, message):
        """ function to define what happens on message """
        print("Received message: " + str(message.payload))

    def on_connect(self, client, userdata, flags, rc):
        """ function to define what happens on connection """
        if rc == 0:
            print("Connected to broker")
            self.connected = True
        else:
            print("Connection failed with error code " + str(rc))

    def on_disconnect(self, client, userdata, rc):
        """ function to define what happens on disconnection """
        print("Disconnected from broker")
        self.connected = False
