<!--
Copyright (c) 2023, Cisco and/or its affiliates.
All rights reserved.
See LICENSE file in this distribution.
SPDX-License-Identifier: Apache-2.0
-->

# TieDie SDK for Python

See accompanying LICENSE file in this distribution.

This distribution contains libraries to enable communications between
applications and IoT devices through an application layer gateway.

## Usage

### Authentication

There are two methods of authentication with TieDie.

1. API key based
2. Certificate based

To authenticate, the CA certificate of the server is also
required to verify the certificate sent by the server.

This file (`ca.pem`) is required by the authenticator.

```
with self.app.open_resource(path.ca.pem, 'rb') as client_keystore_stream:
            client_keystore = client_keystore_stream.read()
```

#### API key authentication

To authenticate using an API key, generate an API key for the client.

```
Authenticator authenticator = ApiKeyAuthenticator.create(caInputStream, "app_id", "api_key");
authenticator = ApiKeyAuthenticator(app_id,  CA_PEM_PATH, app_key)
```

#### Certificate based

To authenticate using a certificate, we use a Java KeyStore to store the certificates
and load the credentials from it.

For example, the keystore can be created using the pkcs #12 format.

The PKCS #12 file (`.p12` or `.pfx`) can be created from the certificate and private key
as follows:

```bash
openssl pkcs12 -export -out client.p12 -inkey client.key -in client.crt
```

An example with a keystore is shown below:

```
with io.open(client_config.CA_PEM_PATH, 'rb') as ca_stream, \
    io.open(client_config.CONTROL_CERT_PATH, 'rb') as client_keystore_stream:
    key_store = KeyStore.getInstance("PKCS12")
    key_store.load(client_keystore_stream, "".toCharArray())
            
    authenticator = ApiKeyAuthenticator.create(ca_stream, control_app_id, endpoint_app.get_client_token())
```

### Onboarding Client

The onboarding client can be created as follows:

```
onboardingClient = OnboardingClient("https://<host>/scim/v2", authenticator);
```

#### Create an Endpoint App

Register an endpoint app using the onboarding app.

```
endpointApps = onboarding_client.getEndpointApps().body["Resources"]

onboarding_client.createEndpointApp({"applicationName": self.control_app_id // self.data_app_id,
                                     "applicationType": "DEVICE_CONTROL" // "applicationType": "TELEMETRY" })
```

#### Onboard a device

```
device = Device(content['deviceDisplayName'], admin_state, BleExtension(content['deviceMacAddress'], version_support, is_random, int(content['passKey'])))

response = onboarding_client.createDevice(device)
```

#### Fetch a device

```
response = onboarding_client.getDevice(id)

device = Device.create(response.body)
```

#### Un-onboard a device

```
response = onboarding_client.deleteDevice(id)
```

### Control Client

The control API client can be created as follows:

```
controlClient = ControlClient(control_base_url, authenticator)
```

You can control a device using the APIs using the corresponding `Device` object.

#### Connect

```
tiedie_response = control_client.connect(device)
```

#### Disconnect

```
tiedie_response = control_client.disconnect(device)
```

#### Read

```
parameter = BleDataParameter(id, svcUUID, charUUID)
response = control_client.read(parameter)
```

#### Write

```
parameter = BleDataParameter(id, svcUUID, charUUID)
response = control_client.write(parameter, value)
```

#### Subscribe

```
parameter = BleDataParameter(id, svcUUID, charUUID)
subscribe = control_client.subscribe(topic, parameter)


```

#### Register Topic

To register a topic on a GATT subscription:

```
topic = f"data-app/{id}/{svcUUID}/{charUUID}"

topic_response = control_client.register_topic(topic, 
                                                   DataRegistrationOptions(
                                                        devices = None,
                                                        dataFormat = DataFormat.JSON,
                                                        dataParameter = parameter)
                                                )
```

To register a topic on advertisements:

```
Ttopic_response = control_client.register_topic(
        topic, 
        AdvertisementRegistrationOptions(
            devices = None,
            dataFormat=DataFormat.JSON,
            advertisementFilterType=request_data['filterType'],
            advertisementFilters=request_data['filters']
        )
    )
```

To register a topic on connection status: 

```
control_client.register_topic(
        topic, 
        ConnectionRegistrationOptions(
            devices=[],
            dataFormat=DataFormat.JSON
        )
    )
```

#### Register Data App

```
topic = "data-app/" + response.body['id'] + "/connection"
dataAppResponse = control_client.register_data_app(app.config['data-app.id'], topic)
```

### Data Receiver Client

The data receiver client can be created as follows:

```
dataReceiverClient = DataReceiverClient(data_base_url,  authenticator=authenticator, port=8883)
dataReceiverClient.connect();
```

#### Subscriptions

```
data_receiver_client.subscribe(topic, callback)
callback -> Handles Message
});
```
