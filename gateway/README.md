<!--
Copyright (c) 2023, Cisco Systems, Inc. and/or its affiliates.
All rights reserved.
See LICENSE file in this distribution.
SPDX-License-Identifier: Apache-2.0
-->

# TieDie Gateway functionality

This directory contains code necessary to run a SCIM and NIPC gateway
as described in [draft-ietf-scim-device-model](https://datatracker.ietf.org/doc/draft-ietf-scim-device-model/)
and [draft-ietf-asdf-nipc](https://datatracker.ietf.org/doc/draft-ietf-asdf-nipc/).

For BLE functionality, the gateway supports two access point backends:

1. Silabs dev kit backend (EFR32xG21, default)
2. Mock backend (no BLE hardware required)

## Setup

Flash the **Bluetooth - NCP** demo binary using Simplicity Studio.
This was tested using Gecko SDK 4.4.1 and on the EFR32xG21 kit.

### Select BLE access point backend

By default, the gateway runs with the Silabs backend (`--device silabs`).
The connection argument can be autodetected or provided explicitly.
Autodetection succeeds only when exactly one supported Silabs serial device is found.

```bash
# Default (autodetect serial connector)
python3 app.py

# Explicit serial connector example
python3 app.py /dev/ttyACM0
```

To run without BLE hardware, use the mock backend:

```bash
python3 app.py --device mock
```

### Configure the gateway

The gateway uses TLS for the SCIM and NIPC APIs.
This requires certificates to be generated and placed in the `ca_certificates` and `certs` directories.

#### Generate a new CA cert for testing

```bash
cd certs
./make-ca-certs.sh
```

#### Generate Server Certs

##### Create server private key and certificate

```bash
cd certs
./gen_cert.sh server
```

### Start the gateway

#### On Linux

On a linux host, where usb passthrough is supported in docker, you can run:

```bash
docker compose up --build
```

This flow is intended for the Silabs backend and maps `/dev/ttyACM0` into the gateway container.
The compose service runs `python3 app.py` (default backend selection), so mock mode is not enabled unless you override the container command.

#### On MacOS

Create a virtual environment and install the requirements:

```bash
python3 -m venv venv
source venv/bin/activate
pip3 install -r requirements.txt
```

Bring up the mosquitto and postgres containers:

```bash
docker compose up mosquitto postgres
```

Run the application:

```bash
python3 app.py
```

To run without BLE hardware:

```bash
python3 app.py --device mock
```

## Generate API keys

To register an onboarding app, run the following command:


```bash
flask --app app register-onboarding-app <onboarding_app_name>
```

To register a control or data app, you can use the `EndpointApps` SCIM APIs.


## Generate client private key and certificate

If you want to use certificates to authenticate the endpoint apps, you can generate them using the same `gen_cert.sh` script.

```bash
cd certs
./gen_cert.sh <client_name>
```

# MAB Support

MAC Authentication Bypass is a primitive and weak form of authentication
that just checks against MAC addresses. Use at your own risk. Any device
can fake a MAC address. However, sometimes it is useful for bootstrapping
stronger trust.

If you want MAB support, you must indicate that by setting appropriate
environment variables in the docker-compose.yml file as follows:


```
WANT_ETHERNET_MAB=True

ISE_HOST={ISE ERS endpoint hostname}
ISE_USERNAME=user
ISE_PASSWORD={whateversecret}
```

By default MAB is not supported. If all three of the ISE environment
variables are not set, the SCIM database will be updated, but nothing
else will be done. In the future, one might expect support for AAA
services other than ISE.

# FDO Support

If you want FDO support, you must indicate that by setting appropriate
environment variables in the docker-compose.yml file as follows:

```
WANT_FDO=True

FDO_OWNER_URI={FDO owner service URI}
FDO_CLIENT_CERT={client certificate setting used for owner service access}
FDO_SERVER_CERT={set to any value to enable TLS server cert verification}
```

By default FDO is not supported. If `WANT_FDO` is not set, the FDO SCIM
extension is rejected. If `WANT_FDO` is set but the owner-service variables
are not fully set, voucher data is still stored in the SCIM database.
