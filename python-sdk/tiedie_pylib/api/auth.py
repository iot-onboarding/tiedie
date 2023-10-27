#!python
# Copyright (c) 2023, Cisco Systems, Inc. and/or its affiliates.
# All rights reserved.
# See LICENSE file in this distribution.
# SPDX-License-Identifier: Apache-2.0

import os
import ssl
import typing
import http.client
import OpenSSL.crypto
from io import BytesIO
from paho.mqtt.client import Client as MqttClient
from requests.models import PreparedRequest


class Authenticator:
    """
    Interface to support different authentication methods.
    """

    SKIP_HOSTNAME_VERIFICATION = True

    def __init__(self, trust_managers: typing.List[ssl.SSLContext]):
        self.trust_managers = trust_managers


    @staticmethod
    def get_key_managers(key_store: ssl.SSLContext, password: str):
        """
        Get KeyManager associated with a KeyStore.

        :param key_store: SSLContext object that has the certificate and private key to be used by the client.
        :param password: Password for the KeyStore object.
        :return: Array of KeyManager objects. Only the first one is used.
        """
        try:
            if password is not None:
                pwd = password.encode()
            else:
                pwd = None

                context = ssl.SSLContext(ssl.PROTOCOL_TLS)
                context.load_cert_chain(certfile=key_store, password=pwd)

                key_manager_factory = context._key_mgr_factory
                return key_manager_factory.get_key_managers()
        except Exception as e:
            raise RuntimeError(e)
        

    @staticmethod
    def get_ca_trust_managers(ca_cert: BytesIO):
        """
        Get TrustManager that represents the Certificate Authority to verify the server certificate.

        :param ca_cert: Byte contents of the CA file in PEM format.
        :return: Array of TrustManager objects. Only the first one is used.
        """
        try:
            trusted_store = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            trusted_store.load_verify_locations(cadata=ca_cert.getvalue().decode("ascii"))

            return trusted_store.get_ca_certs()
        except Exception as e:
            raise RuntimeError(e)
        

    def get_client_id(self) -> str:
        """
        Returns the ID of the client.
        """
        pass


    def set_auth_options(self, builder: object) -> object:
        """
        Update builder object after adding authentication related settings.

        :param builder: OkHttpClient.Builder object.
        :return: Updated builder object after adding authentication related settings.
        """
        pass


    def set_auth_options_mqtt(self, mqtt_connect_options: object):
        """
        Set auth options for the data receiver app.

        :param mqtt_connect_options: MqttConnectOptions object.
        """
        pass


class ApiKeyAuthenticator:
    API_KEY_HEADER = 'x-api-key'
    SKIP_HOSTNAME_VERIFICATION = True

    def __init__(self, app_id, ca_file_path, api_key):
        self.app_id = app_id
        self.api_key = api_key
        self.ca_file_path = ca_file_path

        absolute_ca_file_path = os.path.abspath(ca_file_path)

        with open(absolute_ca_file_path, 'rb') as ca_file:

            self.ca_certs = ca_file.read()

        self.ssl_context = ssl.create_default_context(purpose=ssl.Purpose.SERVER_AUTH, cafile=ca_file_path)


    def get_client_id(self):
        return self.app_id


    def set_auth_options(self, session):
        session.headers[self.API_KEY_HEADER] = self.api_key
        session.verify = False
        return session


    def set_ssl_context(self, conn):
        conn_context = conn.context
        conn_context.check_hostname = not self.SKIP_HOSTNAME_VERIFICATION
        conn_context.verify_mode = ssl.CERT_REQUIRED
        conn_context.load_verify_locations(cadata=self.ca_certs)
        return conn


    def set_ssl_context_mqtt(self, mqtt):
        # mqtt.tls_set(ca_certs=self.ca_file_path)
        # mqtt.tls_insecure_set(self.SKIP_HOSTNAME_VERIFICATION)
        mqtt.username_pw_set(self.app_id, password=self.api_key)
        return mqtt


class CertificateAuthenticator:

    def __init__(self, key_managers: list, trust_managers: list, cn: str) -> None:
        self.key_managers = key_managers
        self.trust_managers = trust_managers
        self.cn = cn


    @staticmethod
    def _get_cn_from_certificate(certificate: bytes) -> str:
        x509 = OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_PEM, certificate)
        subject = x509.get_subject()
        return next((value for short_name, value in subject.get_components() if short_name == b'CN'), None)


    @classmethod
    def create(cls, ca_input_stream: BytesIO, key_store: OpenSSL.crypto.PKey, cert: OpenSSL.crypto.X509) -> 'CertificateAuthenticator':
        key_managers = []
        key_managers.append(ssl.KeyPair(cert, key_store))
        trust_managers = []
        trust_managers.append(ssl.Certificates(ca_input_stream.read(), trust_default_ca=True))
        cn = cls._get_cn_from_certificate(cert.to_cryptography())
        return cls(key_managers, trust_managers, cn)


    def get_client_id(self) -> str:
        return self.cn


    def set_auth_options(self, client: MqttClient) -> None:
        client.tls_set_context(ssl.create_default_context(keyfile=self.key_managers[0].get_privatekey().to_cryptography(), certfile=self.key_managers[0].get_certificate().to_cryptography(), cafile=self.trust_managers[0].get_ca_certificates().to_cryptography(),))


    def set_auth_options(self, http_client: http.client.HTTPSConnection) -> None:
            ssl_context = ssl.create_default_context(purpose=ssl.Purpose.SERVER_AUTH)
            ssl_context.load_cert_chain(certfile=self.key_managers[0].get_certificate().to_cryptography(), keyfile=self.key_managers[0].get_privatekey().to_cryptography())
            ssl_context.load_verify_locations(cafile=self.trust_managers[0].get_ca_certificates().to_cryptography())

            if http_client is not None:
                http_client.ssl_context = ssl_context

    def set_auth_options(self, request: PreparedRequest) -> PreparedRequest:
        request.headers.update({'X-SYSTEM-ID': self.cn})
        return request

