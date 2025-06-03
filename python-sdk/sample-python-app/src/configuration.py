# Copyright (c) 2023, Cisco Systems, Inc. and/or its affiliates.
# All rights reserved.
# See LICENSE file in this distribution.
# SPDX-License-Identifier: Apache-2.0

""" this module configures the TieDie clients """

import base64
from typing import Optional
from flask import Flask
import OpenSSL.crypto
from requests_oauth2client import OAuth2Client
from tiedie.api.onboarding_client import OnboardingClient
from tiedie.api.control_client import ControlClient
from tiedie.api.data_receiver_client import DataReceiverClient
from tiedie.api.auth import ApiKeyAuthenticator, CertificateAuthenticator, OAuth2Authenticator
from tiedie.models.scim import AppCertificateInfo, EndpointApp, EndpointAppType


class ClientConfig:
    """ Client configuration class. """

    def __init__(self, app: Flask):
        self.app = app
        self.client_ca_path = app.config.get('CLIENT_CA_PATH')
        self.onboarding_app_base_url = app.config.get('ONBOARDING_APP_BASE_URL')
        self.onboarding_app_id = app.config.get('ONBOARDING_APP_ID')
        self.onboarding_app_cert_path = app.config.get('ONBOARDING_APP_CERT_PATH')
        self.onboarding_app_key_path = app.config.get('ONBOARDING_APP_KEY_PATH')
        self.onboarding_app_api_key = app.config.get('ONBOARDING_APP_API_KEY')
        self.control_app_base_url = app.config.get('CONTROL_APP_BASE_URL')
        self.control_app_id = app.config.get('CONTROL_APP_ID')
        self.control_app_cert_path = app.config.get('CONTROL_APP_CERT_PATH')
        self.control_app_key_path = app.config.get('CONTROL_APP_KEY_PATH')
        self.data_app_tls_enabled = app.config.get('DATA_APP_TLS_ENABLED')
        self.data_app_tls_self_signed = app.config.get('DATA_APP_TLS_SELF_SIGNED')
        self.data_app_host = app.config.get('DATA_APP_HOST')
        self.data_app_port = app.config.get('DATA_APP_PORT')
        self.data_app_id = app.config.get('DATA_APP_ID')
        self.data_app_username = app.config.get('DATA_APP_USERNAME')
        self.data_app_password = app.config.get('DATA_APP_PASSWORD')
        self.data_app_ca_cert_path = app.config.get('DATA_APP_CA_CERT_PATH')
        self.data_app_mqtt_type = app.config.get('DATA_APP_MQTT_TYPE', 'client')
        self.oauth_client_id = app.config.get('OAUTH_CLIENT_ID')
        self.oauth_client_secret = app.config.get('OAUTH_CLIENT_SECRET')
        self.oauth_auth_endpoint = app.config.get('OAUTH_AUTH_ENDPOINT')
        self.oauth_token_endpoint = app.config.get('OAUTH_TOKEN_ENDPOINT')
        self.oauth_redirect_uri = app.config.get('OAUTH_REDIRECT_URI')
        self.oauth_scopes = app.config.get('OAUTH_SCOPES')
        if self.oauth_client_id is not None:
            # initialize authenticator with OAuth2
            if (self.oauth_auth_endpoint is None or self.oauth_token_endpoint is None or
                self.oauth_client_id is None or self.oauth_client_secret is None or
                self.oauth_redirect_uri is None):
                raise ValueError("OAuth2 endpoints and client ID/secret must be provided.")
            self.oauth2client = OAuth2Client(
                self.oauth_token_endpoint,
                authorization_endpoint=self.oauth_auth_endpoint,
                redirect_uri=self.oauth_redirect_uri,
                auth=(self.oauth_client_id, self.oauth_client_secret),
            )
            self.oauth_authenticator = OAuth2Authenticator(self.oauth2client)

    def get_onboarding_client(self):
        """
        Returns an onboarding client.
        """
        if self.oauth_client_id is not None:
            authenticator = self.oauth_authenticator
        elif self.onboarding_app_cert_path is not None and self.onboarding_app_key_path is not None:
            authenticator = CertificateAuthenticator(
                self.client_ca_path, self.onboarding_app_cert_path, self.onboarding_app_key_path)
        else:
            authenticator = ApiKeyAuthenticator(
                self.onboarding_app_id, self.client_ca_path, self.onboarding_app_api_key)
        return OnboardingClient(self.onboarding_app_base_url, authenticator)

    def get_control_client(self, control_app_endpoint: Optional[EndpointApp]):
        """
        Returns a control client.
        """
        if self.oauth_client_id is not None:
            authenticator = self.oauth_authenticator
        elif control_app_endpoint is not None and control_app_endpoint.certificate_info is not None:
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
                data_app_endpoint.application_id,
                self.client_ca_path,
                data_app_endpoint.client_token
            )
        if self.data_app_mqtt_type == 'broker':
            authenticator = ApiKeyAuthenticator(
                self.data_app_username,
                self.data_app_ca_cert_path,
                self.data_app_password,
            )
        return DataReceiverClient(
            self.data_app_host,
            authenticator=authenticator,
            port=self.data_app_port,
            disable_tls=not self.data_app_tls_enabled,
            insecure_tls=self.data_app_tls_self_signed
        )

    def get_root_ca(self):
        """ Get the root CN from certificate. """
        with open(self.client_ca_path, 'rb') as ca_stream:
            cert = ca_stream.read()
        cert = OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_PEM, cert)
        cert_der = OpenSSL.crypto.dump_certificate(OpenSSL.crypto.FILETYPE_ASN1, cert)
        cert_base64 = base64.b64encode(cert_der).decode('utf-8')
        return cert_base64

    def get_endpoint_apps(self, onboarding_client: OnboardingClient):
        """
        Returns the endpoint apps for the onboarding app.
        """
        http_response = onboarding_client.get_endpoint_apps()
        endpoint_apps = http_response.body.resources or []
        control_app = next((app for app in endpoint_apps
                            if app.application_type == "deviceControl" and
                            app.application_name == self.control_app_id), None)
        if control_app is None and self.oauth_client_id is None:
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
        return [control_app, data_app]
