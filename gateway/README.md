<!--
Copyright (c) 2023, Cisco Systems, Inc. and/or its affiliates.
All rights reserved.
See LICENSE file in this distribution.
SPDX-License-Identifier: Apache-2.0
-->

# TieDie Gateway functionality

This directory contains code necessary to run a SCIM and NIPC gateway
as described in draft-ietf-scim-device-model and draft-brinckman-asdf-nipc.

The gateway also requires a Silabs Dev Kit (EFR32xG21) for the BLE functionality. 

## Setup

Flash the **Bluetooth - NCP** demo binary using Simplicity Studio.  
This was tested using Gecko SDK 4.4.1 and on the EFR32xG21 kit. 

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
<!-- 
To initialize the database, run the following command:
```bash
docker exec -ti ciscoble-tiedie-ap-1 bash -c "flask db init" 
docker exec -ti ciscoble-tiedie-ap-1 bash -c "flask db migrate" 
docker exec -ti ciscoble-tiedie-ap-1 bash -c "flask db upgrade"  
```
-->

#### On MacOS

Create a virtual environment and install the requirements:

```bash
python3 -m venv venv
source venv/bin/activate
pip3 install -r requirements.txt
```

Bring up the mosquitto and postgres containers:

```bash
docker-compose up mosquitto postgres
```
<!-- 
Initialize the database: 

```bash
flask db init
flask db migrate
flask db upgrade
``` -->

Run the application:

```bash
python3 app.py
```

## Generate API keys

To register an onboarding app, run the following command:


```bash
flask register-onboarding-app <onboarding_app_name>
```

To register a control or data app, you can use the `EndpointApps` SCIM APIs. 


## Generate client private key and certificate

If you want to use certificates to authenticate the endpoint apps, you can generate them using the same `gen_cert.sh` script. 

```bash
cd certs
./gen_cert.sh <client_name>
```

# MAB Support

MAC Authentication Bypass is a primative and weak form of authentication
that just checks against MAC addresses.  Use at your own risk.  Any device
can fake a MAC address.  However, sometimes it is useful for bootstrapping
stronger trust.

If you want MAB support, you must indicate that by setting appropriate
environment variables in the docker-compose.yml file as follows:


```
WANT_ETHERNET_MAB=True

ISE_HOST={ISE ERS endpoint hostname}
ISE_USERNAME=user
ISE_PASSWORD={whateversecret}
```

By default MAB is not supported.  If all three of the ISE environment
variables are not set, the SCIM database will be updated, but nothing
else will be done.  In the future, one might expect support for AAA
services other than ISE.


