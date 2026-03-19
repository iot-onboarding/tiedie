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

Using a virtual environment is recommended.
If your system uses `python3` instead of `python`, substitute `python3` in the commands below.

```bash
python -m venv .venv
source .venv/bin/activate

python -m pip install --upgrade pip
python -m pip install .
```

## Usage

### Authentication

There are three methods of authentication with TieDie.

1. API key based
2. Certificate based
3. OAuth2 based

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

#### OAuth2 based

To authenticate using OAuth2 authorization code flow:

```python
from requests_oauth2client import OAuth2Client, OAuth2AuthorizationCodeAuth
from tiedie.api.auth import OAuth2Authenticator

oauth2client = OAuth2Client(
    "<token_endpoint>",
    authorization_endpoint="<authorization_endpoint>",
    redirect_uri="<redirect_uri>",
    auth=("<client_id>", "<client_secret>"),
)

authenticator = OAuth2Authenticator(oauth2client)

# Redirect the user to this URL to authorize.
az_request = oauth2client.authorization_request(scope="<scopes>")
print(az_request.uri)

# After callback, validate the callback URL and set session_auth.
az_response = az_request.validate_callback("<callback_url>")
authenticator.session_auth = OAuth2AuthorizationCodeAuth(
    oauth2client,
    code=az_response,
)
```

The `session_auth` field must be set after the authorization code callback before making API requests with `OAuth2Authenticator`.

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

#### Get endpoint apps

```python
response = onboarding_client.get_endpoint_apps()

assert response.status_code == 200
print(response.body.resources)
```

#### Get one endpoint app

```python
response = onboarding_client.get_endpoint_app(app_id)

assert response.status_code == 200
print(response.body.application_id)
```

#### Onboard a device

```python
from tiedie.models.scim import Device, BleExtension, PairingPassKey

device = Device(
    display_name="BLE Monitor",
    active=False,
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

#### Update a device

```python
device.display_name = "BLE Monitor Updated"
response = onboarding_client.update_device(device)

assert response.status_code == 200
print(response.body.display_name)
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
from tiedie.api.control_client import ControlClient

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

For SDF APIs, `sdf_name` should be the full SDF path, for example:
`https://example.com/heartrate#/sdfObject/healthsensor`.

#### Read

```python
sdf_name = "https://example.com/heartrate#/sdfObject/healthsensor"
response = control_client.read_property(device_id, sdf_name)
```

#### Write

```python
# value must be base64-encoded bytes
response = control_client.write_property(
    device_id,
    sdf_name,
    "<base64_value>"
)
```

#### Get connection state

```python
response = control_client.get_connection(device)
```

#### Discover services and characteristics

```python
response = control_client.discover(device)
```

#### Events

To enable an event for a device:

```python
response = control_client.enable_event(device_id, "<event_name>")
instance_id = response.body
```

To get all enabled events for a device:

```python
response = control_client.get_all_events(device_id)
```

To get one enabled event:

```python
response = control_client.get_event(device_id, instance_id)
```

To disable an event:

```python
response = control_client.disable_event(device_id, instance_id)
```

#### SDF Model Registration APIs

```python
from tiedie.models.requests import SdfModel

model = SdfModel.model_validate_json("<sdf_model_json>")

# Register
register_response = control_client.register_sdf_model(model)

# List all registered models
list_response = control_client.get_sdf_models()

# Fetch one model by SDF name
get_response = control_client.get_sdf_model(sdf_name)

# Update an existing model by SDF name
update_response = control_client.update_sdf_model(sdf_name, model)

# Unregister a model by SDF name
delete_response = control_client.unregister_sdf_model(sdf_name)
```

#### Data App Registration APIs

```python
from tiedie.models.responses import DataAppRegistration, Event

data_app_id = "<data_app_id>"
registration = DataAppRegistration(
    events=[Event(event="<event_name>")],
    mqtt_client=True
)

create_response = control_client.create_data_app(data_app_id, registration)
get_response = control_client.get_data_app(data_app_id)
update_response = control_client.update_data_app(data_app_id, registration)
delete_response = control_client.delete_data_app(data_app_id)
```

### Data Receiver Client

The data receiver client can be created as follows:

```python
from tiedie.api.data_receiver_client import DataReceiverClient

data_receiver_client = DataReceiverClient(
    "<host>",
    authenticator=authenticator,
    port=8883,
    disable_tls=False,
    insecure_tls=True,
)
data_receiver_client.connect()
```

#### Subscriptions

```python
# callback receives CBOR-decoded subscription payload
def callback(data_subscription):
    print(data_subscription)

data_receiver_client.subscribe(topic, callback)
```

To unsubscribe from a topic:

```python
data_receiver_client.unsubscribe(topic)
```

To disconnect the client:

```python
data_receiver_client.disconnect()
```
