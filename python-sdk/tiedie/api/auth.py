#!python
# Copyright (c) 2023, Cisco Systems, Inc. and/or its affiliates.
# All rights reserved.
# See LICENSE file in this distribution.
# SPDX-License-Identifier: Apache-2.0

import OpenSSL.crypto
import paho.mqtt.client as mqtt
import requests


class Authenticator:
    """
    Interface to support different authentication methods.
    """

    SKIP_HOSTNAME_VERIFICATION = True

    def get_client_id(self) -> str:
        """
        Returns the ID of the client.
        """
        raise NotImplementedError()

    def set_auth_options(self, session: requests.Session) -> object:
        """
        Update builder object after adding authentication related settings.

        :param builder: OkHttpClient.Builder object.
        :return: Updated builder object after adding authentication related settings.
        """
        raise NotImplementedError()

    def set_auth_options_mqtt(self, mqtt_client: mqtt.Client):
        """
        Set auth options for the data receiver app.

        :param mqtt_connect_options: MqttConnectOptions object.
        """
        raise NotImplementedError()


class ApiKeyAuthenticator(Authenticator):
    """
    Authenticator implementation for API key based authentication.
    """

    API_KEY_HEADER = 'x-api-key'
    SKIP_HOSTNAME_VERIFICATION = True

    def __init__(self, app_id, ca_file_path, api_key):
        self.app_id = app_id
        self.api_key = api_key
        self.ca_file_path = ca_file_path

    def get_client_id(self):
        return self.app_id

    def set_auth_options(self, session):
        session.headers[self.API_KEY_HEADER] = self.api_key
        session.verify = self.ca_file_path
        return session

    def set_auth_options_mqtt(self, mqtt_client: mqtt.Client):
        mqtt_client.tls_set(ca_certs=self.ca_file_path)
        mqtt_client.username_pw_set(self.app_id, password=self.api_key)
        return mqtt_client


class CertificateAuthenticator(Authenticator):
    """
    Authenticator implementation for certificate based authentication.
    """

    def __init__(self, ca_file_path: str, cert_path: str, key_path: str) -> None:
        self.ca_file_path = ca_file_path
        self.cert_path = cert_path
        self.key_path = key_path

    def get_client_id(self) -> str:
        # return CN from the ca file
        with open(self.cert_path, 'rb') as ca_stream:
            cert = ca_stream.read()

        cert = OpenSSL.crypto.load_certificate(
            OpenSSL.crypto.FILETYPE_PEM, cert)

        return cert.get_subject().CN

    def set_auth_options(self, session: requests.Session) -> object:
        session.verify = self.ca_file_path
        session.cert = (self.cert_path, self.key_path)
        return session

    def set_auth_options_mqtt(self, mqtt_client: mqtt.Client):
        mqtt_client.tls_set(ca_certs=self.ca_file_path,
                            certfile=self.cert_path, keyfile=self.key_path)
        return mqtt_client
