<!--
Copyright (c) 2023, Cisco Systems, Inc. and/or its affiliates.
All rights reserved.
See LICENSE file in this distribution.
SPDX-License-Identifier: Apache-2.0
-->

# TieDie SDK for Python

See accompanying LICENSE file in this distribution.

This distribution contains libraries to enable communications between
applications and IoT devices through an application layer gateway.

## Prerequisites

- Python 3.10 or higher

## Installation

```bash
# Optionally, create a virtual env
python3 -m venv venv
source venv/bin/activate

pip3 install .
```

## Usage

### Authentication

There are two methods of authentication with TieDie.

1. API key based
2. Certificate based

To authenticate, the CA certificate of the server is also
required to verify the certificate sent by the server.

This file (`ca.pem`) is required by the authenticator.

#### API key authentication

To authenticate using an API key, generate an API key for the client.

```python
from tiedie.api.auth import ApiKeyAuthenticator

authenticator = ApiKeyAuthenticator(
    app_id="<app_id>",
    ca_file_path="<client_ca_path>",
    api_key="<api_key>"
)
```

#### Certificate based

To authenticate using a certificate, we need the client certificate and private key. 

```python
from tiedie.api.auth import CertificateAuthenticator

authenticator = CertificateAuthenticator(
    ca_file_path="<client_ca_path>",
    cert_path="<client_cert_path>",
    key_path="<client_key_path>",
)
```

### Onboarding Client

The onboarding client can be created as follows:

```python
from tiedie.api.onboarding_client import OnboardingClient

onboarding_client = OnboardingClient(
    base_url="https://<host>/scim/v2", 
    authenticator=authenticator
)
```

#### Create an Endpoint App

Register an endpoint app using the onboarding app.

```python
from tiedie.models.scim import EndpointApp, EndpointAppType

response = onboarding_client.create_endpoint_app(
    EndpointApp(
        application_name="control-app",
        application_type=EndpointAppType.DEVICE_CONTROL
    )
)

print(response.body.application_name)
print(response.body.application_type)
print(response.body.application_id)
print(response.body.client_token)
```

#### Onboard a device

```python
from tiedie.models.scim import Device, BleExtension, PairingPassKey

device = Device(
    device_display_name="BLE Monitor",
    admin_state=False,
    ble_extension=BleExtension(
        device_mac_address="AA:BB:CC:11:22:33",
        is_random=False,
        version_support=["4.1", "4.2", "5.0", "5.1", "5.2", "5.3"],
        pairing_pass_key=PairingPassKey(key=123456)
    )
)

response = onboarding_client.create_device(device)

print(response.body.device_id)
```

#### Fetch a device

```python
response = onboarding_client.get_device(device_id)

assert response.status_code == 200
print(response.body.device_id)
```

#### Get all devices

```python
response = onboarding_client.get_devices()

assert response.status_code == 200
print(response.body.resources[0].device_id)
```

#### Un-onboard a device

```python
response = onboarding_client.delete_device(device_id)
assert response.status_code == 204
```

### Control Client

The control API client can be created as follows:

```python
control_client = ControlClient(
    base_url="https://<host>/nipc",
    authenticator=authenticator
)
```

You can control a device using the APIs using the corresponding `Device` object.

#### Connect

```python
response = control_client.connect(device)
```

#### Disconnect

```python
response = control_client.disconnect(device)
```

#### Read

```python
from tiedie.models.ble import BleDataParameter

response = control_client.read(device, BleDataParameter(
    device_id=device_id,
    service_id="1800",
    characteristic_id="2a00"
))
```

#### Write

```python
from tiedie.models.ble import BleDataParameter

response = control_client.write(
    device,
    BleDataParameter(
        device_id=device_id,
        service_id="1800",
        characteristic_id="2a00"
    ),
    "00001111")
```

#### Subscribe

```python
from tiedie.models.ble import BleDataParameter

response = control_client.subscribe(
    device,
    BleDataParameter(
        device_id=device_id,
        service_id="1800",
        characteristic_id="2a00"
    )
)
```

#### Unsubscribe

```python
from tiedie.models.ble import BleDataParameter

response = control_client.unsubscribe(
    device,
    BleDataParameter(
        device_id=device_id,
        service_id="1800",
        characteristic_id="2a00"
    )
)
```

#### Register Topic

To register a topic on a GATT subscription:

```python
from tiedie.models.common import DataRegistrationOptions
from tiedie.models.ble import BleDataParameter

response = control_client.register_topic(topic, device, DataRegistrationOptions(
        data_apps=["app1", "app2"],
        data_parameter=BleDataParameter(
            device_id=device_id, service_id="1800", characteristic_id="2a00")
    )
)
```

To register a topic on advertisements for onboarded devices:

```python
from tiedie.models.ble import AdvertisementRegistrationOptions

response = control_client.register_topic(
    topic, device, AdvertisementRegistrationOptions(
        data_apps=["app1", "app2"]
    )
)
```

To register a topic on advertisements for non-onboarded devices:

```python
from tiedie.models.ble import AdvertisementRegistrationOptions, BleAdvertisementFilter, BleAdvertisementFilterType

response = control_client.register_topic(topic, None, AdvertisementRegistrationOptions(
        data_apps=["app1", "app2"],
        advertisement_filter_type=BleAdvertisementFilterType.ALLOW,
        advertisement_filter=[
            BleAdvertisementFilter(mac="1800", ad_type="2a00", ad_data="0001"),
            BleAdvertisementFilter(mac="1800", ad_type="2a01", ad_data="0002")
        ]
    )
)
```

To register a topic on connection status: 

```python
from tiedie.models.common import ConnectionRegistrationOptions

response = control_client.register_topic(topic, device, ConnectionRegistrationOptions(
        data_apps=["app1", "app2"],
    )
)
```

### Data Receiver Client

The data receiver client can be created as follows:

```python
data_receiver_client = DataReceiverClient("<host>"
                                  authenticator=authenticator,
                                  port=8883,
                                  disable_tls=False,
                                  insecure_tls=True)
data_receiver_client.connect()
```

#### Subscriptions

```python
# callback which receives the subscription message protobuf
def callback(data_subscription):
    print(data_subscription)

data_receiver_client.subscribe(topic, callback)
```

To disconnect the client:

```python
data_receiver_client.disconnect()
```
