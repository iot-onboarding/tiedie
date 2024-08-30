#!python
# Copyright (c) 2023, Cisco Systems, Inc. and/or its affiliates.
# All rights reserved.
# See LICENSE file in this distribution.
# SPDX-License-Identifier: Apache-2.0

"""

The mmodule defines a Python client using Paho MQTT for receiving and 
handling data from an MQTT broker, particularly for IoT applications.

"""

from typing import Any, Callable
import paho.mqtt.client as mqtt
import cbor2
from .auth import Authenticator


class DataReceiverClient:
    """ class DataReceiverClient """

    def __init__(self,
                 host: str,
                 authenticator: Authenticator,
                 port: int = 8883,
                 disable_tls: bool = False,
                 insecure_tls: bool = False):
        self.host = host
        self.port = port
        self.authenticator = authenticator
        self.mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2,
            authenticator.get_client_id(), True)
        self.authenticator.set_auth_options_mqtt(self.mqtt_client, disable_tls, insecure_tls)
        self.mqtt_client.on_connect = self.__on_connect
        self.mqtt_client.on_disconnect = self.__on_disconnect
        self.mqtt_client.on_message = self.__on_message
        self.connected = False

    def connect(self):
        """ Connect to the MQTT broker """
        self.mqtt_client.connect(self.host, self.port, 60)
        self.mqtt_client.loop_start()

    def disconnect(self):
        """ Disconnect from the MQTT broker """
        self.mqtt_client.disconnect()
        self.mqtt_client.loop_stop()

    def subscribe(self, topic: str,
                  callback: Callable[[Any], None]):
        """ Subscribe to a topic and register a callback function.

        Args:
            topic (str): The topic to subscribe to.
            callback (Callable[[Any], None]): 
                A callback function to be called when a message is received.
        """
        def on_message(_client, _userdata, msg):
            payload = msg.payload
            # data_subscription = data_app_pb2.DataSubscription()
            # data_subscription.ParseFromString(payload)
            print("Received message: ", len(payload), payload.hex())
            data = cbor2.loads(payload)
            callback(data)

        self.mqtt_client.subscribe(topic, qos=0)
        self.mqtt_client.message_callback_add(topic, on_message)

    def unsubscribe(self, topic: str):
        """ Unsubscribe from a topic.

        Args:
            topic (str): The topic to unsubscribe from.
        """
        self.mqtt_client.unsubscribe(topic)

    def __on_message(self, _userdata, message):
        print("Received message: " + str(message.payload))

    def __on_connect(self, _client, _userdata, _connect_flags, reason_code, _properties):
        if reason_code == 0:
            print("Connected to broker")
            self.connected = True
        else:
            print("Connection failed with error code " + str(reason_code))

    def __on_disconnect(self, _client, _userdata, _flags, _reason_code, _properties):
        print("Disconnected from broker")
        self.connected = False
