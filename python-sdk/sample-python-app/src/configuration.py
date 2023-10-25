#
# Copyright (c) 2023, Cisco Systems, Inc. and/or its affiliates.
# All rights reserved.
#
# See accompanying LICENSE file in this distribution
#


from flask import Flask

from tiedie_pylib.api.onboardingclient import OnboardingClient
from tiedie_pylib.api.controlclient import ControlClient
from tiedie_pylib.api.datareceiverclient import DataReceiverClient 
from tiedie_pylib.api.auth import ApiKeyAuthenticator
from tiedie_pylib.models.scim import EndpointApp


class ClientConfig:
    
    def __init__(self, app: Flask):
        self.app = app
        self.data_app_key = app.config.get('DATA_APP_TOKEN')
        self.onb_app_key = app.config.get('ONB_API_KEY')
        self.data_app_id = app.config.get('DATA_APP_ID')
        self.control_app_id = app.config.get('CONTROL_APP_ID')
        self.onboarding_url = app.config.get('ONBOARDING_URL')
        self.control_url = app.config.get('CONTROL_URL')
        self.data_url = app.config.get('DATA_URL')
        self.data_app_port = app.config.get('DATA_APP_PORT', 8883)
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
        authenticator = ApiKeyAuthenticator(self.data_app_id,  self.ca_pem_path, self.onb_app_key)

        return OnboardingClient(self.onboarding_url, authenticator)

    def get_control_client(self, control_app_key):
        '''
        with self.app.open_resource(CA_PEM_PATH, 'rb') as ca_stream:
            ca_cert = ca_stream.read()

        with self.app.open_resource(CONTROL_CERT_PATH, 'rb') as client_keystore_stream:
            client_keystore = client_keystore_stream.read()

        key_store = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
        key_store.load_cert_chain(certfile=BytesIO(client_keystore), password="")
        '''
        authenticator = ApiKeyAuthenticator(self.control_app_id,  self.ca_pem_path, control_app_key)

        return ControlClient(self.control_url, authenticator)


    def get_data_receiver_client(self, data_app_key) -> DataReceiverClient:

        authenticator = ApiKeyAuthenticator(self.data_app_id,  self.ca_pem_path, data_app_key)

        return DataReceiverClient(self.data_url,  authenticator=authenticator, port=self.data_app_port)

   
