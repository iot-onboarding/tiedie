#
# Copyright (c) 2023, Cisco Systems, Inc. and/or its affiliates.
# All rights reserved.
#
# See LICENSE file in this distribution.
# SPDX-License-Identifier: Apache-2.0
#


from flask import Flask

from tiedie_pylib.api.onboardingclient import OnboardingClient
from tiedie_pylib.api.controlclient import ControlClient
from tiedie_pylib.api.datareceiverclient import DataReceiverClient 
from tiedie_pylib.api.auth import ApiKeyAuthenticator


class ClientConfig:
    
    def __init__(self, app: Flask):
        self.app = app
        self.data_app_key = app.config.get('API_KEY')
        self.data_app_id = app.config.get('DATA_APP_ID')
        self.control_app_id = app.config.get('CONTROL_APP_ID')
        self.onboarding_url = app.config.get('ONBOARDING_URL')
        self.control_url = app.config.get('CONTROL_URL')
        self.data_url = app.config.get('DATA_URL')
        self.ca_pem_path = app.config.get('CA_PEM_PATH')

    def get_onboarding_client(self):
        '''
        with self.app.open_resource(CA_PEM_PATH, 'rb') as ca_stream:
            ca_cert = ca_stream.read()

        with self.app.open_resource(ONBOARDING_CERT_PATH, 'rb') as client_keystore_stream:
            client_keystore = client_keystore_stream.read()

        key_store = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
        key_store.load_cert_chain(certfile=BytesIO(client_keystore), password="")
        '''
        authenticator = ApiKeyAuthenticator(self.data_app_id,  self.ca_pem_path, self.data_app_key)

        return OnboardingClient(self.onboarding_url, authenticator)

    def get_control_client(self):
        '''
        with self.app.open_resource(CA_PEM_PATH, 'rb') as ca_stream:
            ca_cert = ca_stream.read()

        with self.app.open_resource(CONTROL_CERT_PATH, 'rb') as client_keystore_stream:
            client_keystore = client_keystore_stream.read()

        key_store = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
        key_store.load_cert_chain(certfile=BytesIO(client_keystore), password="")
        '''
        authenticator = ApiKeyAuthenticator(self.control_app_id,  self.ca_pem_path, self.data_app_key)

        return ControlClient(self.control_url, authenticator)


    def get_data_receiver_client(self) -> DataReceiverClient:

        authenticator = ApiKeyAuthenticator(self.data_app_id,  self.ca_pem_path, self.data_app_key)

        return DataReceiverClient(self.data_url,  authenticator=authenticator, port=8883)

    def getEndpointApps(self, onboarding_client):
        httpResponse = onboarding_client.getEndpointApps()
        endpointApps = httpResponse.body["Resources"]
        if endpointApps is None:
            endpointApps = []

        controlApp = next((app for app in endpointApps if app["applicationType"] == "deviceControl"
                            and app["applicationName"] == self.control_app_id ), None)

        if controlApp is None:
            createEndpointAppResponse = onboarding_client.createEndpointApp({"applicationName": self.control_app_id ,
                                                                            "applicationType": "deviceControl"})
            controlApp = createEndpointAppResponse.body

        dataApp = next((app for app in endpointApps if app["applicationType"] == "telemetry"
                        and app["applicationName"] == self.data_app_id), None)

        if dataApp is None:
            createEndpointAppResponse = onboarding_client.createEndpointApp({"applicationName": self.data_app_id,
                                                                            "applicationType": "telemetry"})
            dataApp = createEndpointAppResponse.body

        print("Control App: ", controlApp)
        print("Data App: ", dataApp)

        return [controlApp, dataApp]
