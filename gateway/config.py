# Copyright (c) 2023, Cisco Systems, Inc. and/or its affiliates.
# All rights reserved.
# See LICENSE file in this distribution.
# SPDX-License-Identifier: Apache-2.0

"""

This code sets configuration parameters using environment variables or
default values for various components and services like MQTT, PostgreSQL,
and timeouts.

"""

import os

SL_BT_CONFIG_MAX_CONNECTIONS = 32

BOOT_TIMEOUT = int(os.getenv("BOOT_TIMEOUT", "5"))
CONNECTION_TIMEOUT = int(os.getenv("CONNECTION_TIMEOUT", "5"))
MQTT_HOST = os.getenv("MQTT_HOST", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", "8883"))
POSTGRES_USER = os.getenv("POSTGRES_USER", "root")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "password")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DB", "tiedie")
EXTERNAL_HOST = os.getenv("EXTERNAL_HOST", "localhost")
EXTERNAL_PORT = os.getenv("EXTERNAL_PORT", "8080")
CDKM_ENDPOINT = os.getenv("CDKM_ENDPOINT", None )
ISE_USERNAME = os.getenv('ISE_USERNAME',None)
ISE_PASSWORD = os.getenv('ISE_PASSWORD',None)
ISE_HOST = os.getenv('ISE_HOST', None)
WANT_ETHER_MAB = os.getenv('WANT_ETHERNET_MAB', None)
WANT_FDO = os.getenv('WANT_FDO',None)
FDO_OWNER_URI = os.getenv('FDO_OWNER_URI',None)
FDO_CLIENT_CERT = os.getenv('FDO_CLIENT_CERT',None)
FDO_CA_CERT = os.getenv('FDO_SERVER_CERT',None)
FDO_SUPPORT = FDO_OWNER_URI is not None and FDO_CLIENT_CERT is not None

ISE_SUPPORT = ISE_USERNAME is not None and ISE_PASSWORD is not None and \
    ISE_HOST is not None
