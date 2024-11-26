# Copyright (c) 2023, Cisco Systems, Inc. and/or its affiliates.
# All rights reserved.
# See LICENSE file in this distribution.
# SPDX-License-Identifier: Apache-2.0

""" this module configures the TieDie clients """


import base64
from flask import Flask

import OpenSSL.crypto
from tiedie.api.onboarding_client import OnboardingClient
from tiedie.api.control_client import ControlClient
from tiedie.api.data_receiver_client import DataReceiverClient
from tiedie.api.auth import ApiKeyAuthenticator, CertificateAuthenticator
from tiedie.models.scim import AppCertificateInfo, EndpointApp, EndpointAppType


class ClientConfig:
    """ Client configuration class. """

    def __init__(self, app: Flask):
        self.app = app

        self.client_ca_path = app.config.get('CLIENT_CA_PATH')
        self.onboarding_app_base_url = app.config.get(
            'ONBOARDING_APP_BASE_URL')
        self.onboarding_app_id = app.config.get('ONBOARDING_APP_ID')
        self.onboarding_app_cert_path = app.config.get(
            'ONBOARDING_APP_CERT_PATH')
        self.onboarding_app_key_path = app.config.get(
            'ONBOARDING_APP_KEY_PATH')
        self.onboarding_app_api_key = app.config.get('ONBOARDING_APP_API_KEY')
        self.control_app_base_url = app.config.get('CONTROL_APP_BASE_URL')
        self.control_app_id = app.config.get('CONTROL_APP_ID')
        self.control_app_cert_path = app.config.get('CONTROL_APP_CERT_PATH')
        self.control_app_key_path = app.config.get('CONTROL_APP_KEY_PATH')
        self.data_app_tls_enabled = app.config.get('DATA_APP_TLS_ENABLED')
        self.data_app_tls_self_signed = app.config.get(
            'DATA_APP_TLS_SELF_SIGNED')

        self.data_app_host = app.config.get('DATA_APP_HOST')
        self.data_app_port = app.config.get('DATA_APP_PORT')
        self.data_app_id = app.config.get('DATA_APP_ID')

    def get_onboarding_client(self):
        """
        Returns an onboarding client.
        """
        if self.onboarding_app_cert_path is not None and self.onboarding_app_key_path is not None:
            # initialize authenticator with certificate
            authenticator = CertificateAuthenticator(
                self.client_ca_path, self.onboarding_app_cert_path, self.onboarding_app_key_path)
        else:
            authenticator = ApiKeyAuthenticator(
                self.onboarding_app_id, self.client_ca_path, self.onboarding_app_api_key)

        return OnboardingClient(self.onboarding_app_base_url, authenticator)

    def get_control_client(self, control_app_endpoint: EndpointApp):
        """
        Returns a control client.
        """
        if control_app_endpoint.certificate_info is not None:
            authenticator = CertificateAuthenticator(
                self.client_ca_path, self.control_app_cert_path, self.control_app_key_path)
        else:
            authenticator = ApiKeyAuthenticator(
                self.control_app_id, self.client_ca_path, control_app_endpoint.client_token)

        return ControlClient(self.control_app_base_url, authenticator)

    def get_data_receiver_client(self, data_app_endpoint: EndpointApp) -> DataReceiverClient:
        """
        Returns a data receiver client.
        """
        if data_app_endpoint.certificate_info is not None:
            authenticator = CertificateAuthenticator(
                self.client_ca_path, self.control_app_cert_path, self.control_app_key_path)
        else:
            authenticator = ApiKeyAuthenticator(
                data_app_endpoint.application_id, self.client_ca_path, data_app_endpoint.client_token)

        return DataReceiverClient(self.data_app_host,
                                  authenticator=authenticator,
                                  port=self.data_app_port,
                                  disable_tls=not self.data_app_tls_enabled,
                                  insecure_tls=self.data_app_tls_self_signed)

    def get_root_ca(self):
        """ Get the root CN from certificate. """
        with open(self.client_ca_path, 'rb') as ca_stream:
            cert = ca_stream.read()

        cert = OpenSSL.crypto.load_certificate(
            OpenSSL.crypto.FILETYPE_PEM, cert)

        # Convert the certificate to DER format
        cert_der = OpenSSL.crypto.dump_certificate(OpenSSL.crypto.FILETYPE_ASN1, cert)

        # Encode the DER byte string to a base64 string
        cert_base64 = base64.b64encode(cert_der).decode('utf-8')

        return cert_base64

# Now pubkey_base64 contains the base64 encoded public key

    def get_endpoint_apps(self, onboarding_client: OnboardingClient):
        """ 
        Returns the endpoint apps for the onboarding app.
        """
        http_response = onboarding_client.get_endpoint_apps()
        endpoint_apps = http_response.body.resources
        if endpoint_apps is None:
            endpoint_apps = []

        control_app = next((app for app in endpoint_apps
                            if app.application_type == "deviceControl" and
                            app.application_name == self.control_app_id), None)

        if control_app is None:
            # create certificateInfo only if certs exist
            certificate_info = None
            if self.control_app_cert_path is not None and self.control_app_key_path is not None:
                certificate_info = AppCertificateInfo(
                    root_ca=self.get_root_ca(),
                    subject_name=self.control_app_id
                )

            endpoint_app_response = onboarding_client.create_endpoint_app(EndpointApp(
                application_name=self.control_app_id,
                certificate_info=certificate_info,
                application_type=EndpointAppType.DEVICE_CONTROL
            ))
            control_app = endpoint_app_response.body

        data_app = next((app for app in endpoint_apps if app.application_type == "telemetry"
                        and app.application_name == self.data_app_id), None)

        if data_app is None:
            endpoint_app_response = onboarding_client.create_endpoint_app(EndpointApp(
                application_name=self.data_app_id,
                application_type=EndpointAppType.TELEMETRY
            ))
            data_app = endpoint_app_response.body

        print("Control App: ", control_app)
        print("Data App: ", data_app)

        return [control_app, data_app]
