# TieDie Gateway functionality

This directory contains code necessary to run a SCIM and NIPC gateway
as described in draft-ietf-scim-device-model and draft-brinckman-asdf-nipc.


## Setup

Flash the **Bluetooth - NCP** demo binary using Simplicity Studio.  
This was tested using Gecko SDK 4.2.1 and on the EFR32xG21 kit. 

### On Linux

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

### On MacOS

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


```
flask register-onboarding-app <onboarding_app_name>
```

To register a control or data app, you can use the `EndpointApps` SCIM APIs. 

## Generate a new CA cert for testing

```cd certs
   sh make-ca-certs.sh
```

## Generate Server Certs

### Create server private key and certificate

```cd certs
  ./gen_cert server
```

## Generate Client Certs

```cd certs
   ./gen_cert client
```

