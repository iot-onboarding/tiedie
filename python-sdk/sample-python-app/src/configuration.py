#
# Copyright (c) 2023, Cisco Systems, Inc. and/or its affiliates.
# All rights reserved.
#
# See LICENSE file in this distribution.
# SPDX-License-Identifier: Apache-2.0
#


from flask import Flask

import OpenSSL.crypto
from tiedie.api.onboardingclient import OnboardingClient
from tiedie.api.controlclient import ControlClient
from tiedie.api.datareceiverclient import DataReceiverClient
from tiedie.api.auth import ApiKeyAuthenticator, CertificateAuthenticator


class ClientConfig:

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
                self.data_app_id,  self.client_ca_path, self.onboarding_app_api_key)

        return OnboardingClient(self.onboarding_app_base_url, authenticator)

    def get_control_client(self, control_app_endpoint: dict):
        """
        Returns a control client.
        """
        if "certificateInfo" in control_app_endpoint:
            authenticator = CertificateAuthenticator(
                self.client_ca_path, self.control_app_cert_path, self.control_app_key_path)
        else:
            authenticator = ApiKeyAuthenticator(
                self.control_app_id,  self.client_ca_path, control_app_endpoint["clientToken"])

        return ControlClient(self.control_app_base_url, authenticator)

    def get_data_receiver_client(self, data_app_endpoint: dict) -> DataReceiverClient:
        """
        Returns a data receiver client.
        """
        if "certificateInfo" in data_app_endpoint:
            authenticator = CertificateAuthenticator(
                self.client_ca_path, self.control_app_cert_path, self.control_app_key_path)
        else:
            authenticator = ApiKeyAuthenticator(
                self.data_app_id,  self.client_ca_path, data_app_endpoint["clientToken"])

        return DataReceiverClient(self.data_app_host,  authenticator=authenticator, port=self.data_app_port, disable_tls=not self.data_app_tls_enabled)
    
    def get_root_cn(self):
        with open(self.client_ca_path, 'rb') as ca_stream:
            cert = ca_stream.read()

        cert = OpenSSL.crypto.load_certificate(
            OpenSSL.crypto.FILETYPE_PEM, cert)

        return cert.get_subject().CN

    def get_endpoint_apps(self, onboarding_client: OnboardingClient):
        """ 
        Returns the endpoint apps for the onboarding app.
        """
        http_response = onboarding_client.getEndpointApps()
        endpoint_apps = http_response.body["Resources"]
        if endpoint_apps is None:
            endpoint_apps = []

        control_app = next((app for app in endpoint_apps if app["applicationType"] == "deviceControl"
                           and app["applicationName"] == self.control_app_id), None)

        if control_app is None:
            # create certificateInfo only if certs exist
            certificate_info = None
            if self.control_app_cert_path is not None and self.control_app_key_path is not None:
                certificate_info = {
                    "rootCN": self.get_root_cn(),
                    "subjectName": self.control_app_id
                }

            endpoint_app_response = onboarding_client.createEndpointApp({"applicationName": self.control_app_id,
                                                                         "certificateInfo": certificate_info,
                                                                         "applicationType": "deviceControl"})
            control_app = endpoint_app_response.body

        data_app = next((app for app in endpoint_apps if app["applicationType"] == "telemetry"
                        and app["applicationName"] == self.data_app_id), None)

        if data_app is None:
            endpoint_app_response = onboarding_client.createEndpointApp({"applicationName": self.data_app_id,
                                                                         "applicationType": "telemetry"})
            data_app = endpoint_app_response.body

        print("Control App: ", control_app)
        print("Data App: ", data_app)

        return [control_app, data_app]
