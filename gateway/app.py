# Copyright (c) 2023, Cisco Systems, Inc. and/or its affiliates.
# All rights reserved.
# See LICENSE file in this distribution.
# SPDX-License-Identifier: Apache-2.0

"""

This script configures components, like MQTT and PostgreSQL, initializes them,
and serves a secure Flask web application with MQTT and BLE integration.

"""

import datetime
import uuid
import ssl

import click
import paho.mqtt.client as mqtt
from sqlalchemy import select

from config import (BOOT_TIMEOUT, MQTT_HOST, MQTT_PORT, POSTGRES_DB,
                    POSTGRES_HOST, POSTGRES_PASSWORD, POSTGRES_PORT,
                    POSTGRES_USER)
from control import PeerCertWSGIRequestHandler
import ap_factory
from data_producer import DataProducer
from database import db, session
from models import EndpointApp, OnboardingAppKey
from util import make_hash
from app_factory import create_app
# pylint: disable-next=unused-import
from scim_ethermab import EtherMABExtension
# pylint: disable-next=unused-import
from scim_fdo import FDOExtension

app = create_app((
    'postgresql+psycopg2://'
    f'{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}'
))

@app.cli.command("register-onboarding-app")
@click.argument("name")
def onboarding_apiauth(name):
    """ Defines authentication during onboarding """
    key = uuid.uuid4()
    authkey = OnboardingAppKey(name, str(key))
    db.session.add(authkey)
    db.session.commit()
    print(name, " API-KEY:", key)


def mqtt_connect() -> mqtt.Client:
    """ Function MQTT connect """
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.tls_set(ca_certs="ca_certificates/ca.pem")
    client.tls_insecure_set(True)
    client.username_pw_set("admin", "admin")
    client.connect(MQTT_HOST, MQTT_PORT, 60)

    return client


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        # if endpointApp doesn't exist, create it
        if not session.scalar(select(EndpointApp).filter_by(applicationName="admin")):
            endpoint_app = EndpointApp()
            endpoint_app.applicationType = "telemetry"
            endpoint_app.applicationName = "admin"
            endpoint_app.password = make_hash("admin")
            endpoint_app.is_admin = True
            endpoint_app.createdTime = datetime.datetime.now()
            endpoint_app.modifiedTime = datetime.datetime.now()

            session.merge(endpoint_app)
            session.commit()

    mqtt_client = mqtt_connect()
    mqtt_client.loop_start()

    data_producer = DataProducer(mqtt_client, app)

    ble_ap = ap_factory.create_ble_ap(data_producer)
    ble_ap.start()

    if not ble_ap.ready.wait(timeout=BOOT_TIMEOUT):
        ble_ap.stop()
        mqtt_client.loop_stop()
        raise RuntimeError("Failed to boot")

    ble_ap.start_scan()

    context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
    context.verify_mode = ssl.CERT_OPTIONAL
    context.load_verify_locations('ca_certificates/ca.pem')
    context.load_cert_chain('certs/server.crt', 'certs/server.key')

    app.run(host="0.0.0.0", port=8081, ssl_context=context,
            request_handler=PeerCertWSGIRequestHandler)

    ble_ap.stop()
    mqtt_client.loop_stop()
