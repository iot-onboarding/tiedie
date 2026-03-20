<!--
Copyright (c) 2023, Cisco Systems, Inc. and/or its affiliates.
All rights reserved.
See LICENSE file in this distribution.
SPDX-License-Identifier: Apache-2.0
-->

# TieDie SDK for Java

This SDK is used to access IOT devices via the virtualized interfaces
for BLE.  A sample application making use of the SDK can be found in
./sample-java-app.

## Prerequisites

The Java SDK can be consumed by Java version 11 or later.
The sample application in `./sample-java-app` requires Java 17.

## Build 

All instructions for building the SDK take place in the SDK directory.

```bash
cd ./sdk
./gradlew build
```

You can find the SDK JAR at `build/libs/tiedie-sdk-java-1.0.jar`.

## Usage

### Authentication

There are three methods of authentication with TieDie.

1. API key based
2. Certificate based
3. OAuth2 bearer token based

To authenticate, the CA certificate of the server is also
required to verify the certificate sent by the server.

This file (`ca.pem`) is required by the authenticator.

```java
FileInputStream caInputStream = new FileInputStream("/path/to/ca.pem");
```

#### API key authentication

To authenticate using an API key, generate an API key for the client.

```java
Authenticator authenticator = ApiKeyAuthenticator.create(caInputStream, "app_id", "api_key");
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

```java
FileInputStream clientKeystoreStream = new FileInputStream("/path/to/client.p12");
KeyStore keyStore = KeyStore.getInstance("PKCS12");
keyStore.load(clientKeystoreStream, "password".toCharArray());

Authenticator authenticator = CertificateAuthenticator.create(caInputStream, keyStore, "password");
```

#### OAuth2 bearer token based

To authenticate using OAuth2 bearer tokens, create an authenticator with an OAuth client ID
and a token supplier that returns the current access token.

```java
Supplier<String> tokenSupplier = () -> getAccessToken();

// Option 1: Use a CA PEM stream for TLS trust
try (InputStream caInputStream = new FileInputStream("/path/to/ca.pem")) {
    Authenticator authenticator = OAuth2Authenticator.create(caInputStream, "client_id", tokenSupplier);
}

// Option 2: Use the JVM default trust store
Authenticator authenticator = OAuth2Authenticator.create("client_id", tokenSupplier);
```

### Onboarding Client

The onboarding client can be created as follows:

```java
 OnboardingClient onboardingClient = new OnboardingClient("https://<host>/scim/v2", authenticator);
```

#### Create an Endpoint App

Register an endpoint app using the onboarding app.

```java
EndpointApp endpointApp = EndpointApp.builder()
        .applicationName("control-app")
        .applicationType(EndpointAppType.DEVICE_CONTROL) // or EndpointAppType.TELEMETRY 
        .build();

HttpResponse<EndpointApp> response = onboardingClient.createEndpointApp(endpointApp);
endpointApp = response.getBody();

var authenticator = ApiKeyAuthenticator.create(caInputStream, "control-app", endpointApp.getClientToken());
```

#### Onboard a device

```java
Device device = Device.builder()
        .displayName("BLE Monitor")
        .active(false)
        .bleExtension(BleExtension.builder()
            .deviceMacAddress("AA:BB:CC:11:22:33")
            .isRandom(false)
            .versionSupport(Arrays.asList("4.1", "4.2", "5.0", "5.1", "5.2", "5.3"))
            .pairingPassKey(new BleExtension.PairingPassKey(123456))
            .build())
        .endpointAppsExtension(
            new EndpointAppsExtension(List.of(endpointApp))
        )
        .build();
        
HttpResponse<Device> response = onboardingClient.createDevice(device);
Device newDevice = response.getBody();
```

#### Fetch a device

```java
HttpResponse<Device> response = onboardingClient.getDevice(deviceId);
Device device = response.getBody();
```

#### Un-onboard a device

```java
HttpResponse<Void> response = onboardingClient.deleteDevice(deviceId);
```

### Control Client

The control API client can be created as follows:

```java
ControlClient controlClient = new ControlClient("https://<host>/nipc", authenticator);
```

You can control a device using the APIs using the corresponding `Device` object.

#### Connect

```java
NipcResponse<List<DataParameter>> response = controlClient.connect(device);
```

#### Disconnect

```java
NipcResponse<TiedieDeviceResponse> response = controlClient.disconnect(device);
```

#### BLE Read

```java
NipcResponse<DataResponse> response = controlClient.read(device, serviceId, characteristicId);
```

#### BLE Write

```java
NipcResponse<DataResponse> response = controlClient.write(device, serviceId, characteristicId, value);
```

#### Discover

```java
NipcResponse<List<DataParameter>> response = controlClient.discover(device);
```

#### Get Connection

```java
NipcResponse<List<DataParameter>> response = controlClient.getConnection(device);
```

For SDF APIs, `sdfName` should be the full SDF path, for example:
`https://example.com/heartrate#/sdfObject/healthsensor`.

#### SDF Property Read

```java
String sdfName = "https://example.com/heartrate#/sdfObject/healthsensor";
NipcResponse<List<PropertyReadResult>> response = controlClient.readProperty(deviceId, sdfName);
```

#### SDF Property Write

```java
String sdfName = "https://example.com/heartrate#/sdfObject/healthsensor";
NipcResponse<List<PropertyWriteResult>> response = controlClient.writeProperty(deviceId, sdfName, value);
```

#### SDF Model Registration APIs

Use these APIs to register SDF models and manage them (create/read/update/delete):

```java
SdfModel model = ...;
String sdfName = "https://example.com/heartrate#/sdfObject/healthsensor";

// Create
NipcResponse<List<ModelRegistrationResponse>> registerResponse = controlClient.registerSdfModel(model);

// Read all
NipcResponse<List<ModelRegistrationResponse>> listResponse = controlClient.getSdfModels();

// Read one
NipcResponse<SdfModel> getResponse = controlClient.getSdfModel(sdfName);

// Update
NipcResponse<ModelRegistrationResponse> updateResponse = controlClient.updateSdfModel(sdfName, model);

// Delete
NipcResponse<ModelRegistrationResponse> deleteResponse = controlClient.unregisterSdfModel(sdfName);
```

#### Get Data App

```java
NipcResponse<DataAppRegistration> response = controlClient.getDataApp("data-app");
```

#### Register Data App

```java
DataAppRegistration dataAppRegistration = new DataAppRegistration();
dataAppRegistration.setMqttClient(true);

NipcResponse<DataAppRegistration> response = controlClient.createDataApp("data-app", dataAppRegistration);
```

#### Update Data App

```java
DataAppRegistration dataAppRegistration = new DataAppRegistration();
dataAppRegistration.setMqttClient(true);

NipcResponse<DataAppRegistration> response = controlClient.updateDataApp("data-app", dataAppRegistration);
```

#### Un-register Data App

```java
NipcResponse<DataAppRegistration> response = controlClient.deleteDataApp("data-app");
```

#### Event APIs

```java
NipcResponse<String> enableResponse = controlClient.enableEvent(deviceId, eventName);
String instanceId = enableResponse.getBody();

NipcResponse<List<TiedieEventResponse>> eventResponse = controlClient.getEvent(deviceId, instanceId);
NipcResponse<List<TiedieEventResponse>> allEventsResponse = controlClient.getAllEvents(deviceId);

NipcResponse<Void> disableResponse = controlClient.disableEvent(deviceId, instanceId);
```

### Data Receiver Client

The data receiver client can be created as follows:

```java
DataReceiverClient dataReceiverClient = new DataReceiverClient("ssl://<host>:8883", authenticator);
dataReceiverClient.connect();
```

#### Subscriptions

```java
dataReceiverClient.subscribe("<topic>", (DataSubscription dataSubscription) -> {
    // ... Handle the advertisement                
});
```

#### Multi-topic Subscriptions

```java
dataReceiverClient.subscribe(List.of("topic/a", "topic/b"), (dataSubscription, topic) -> {
    // ... Handle subscription payload and source topic
});
```

#### Unsubscribe

```java
dataReceiverClient.unsubscribe("topic/a");
dataReceiverClient.unsubscribe(List.of("topic/a", "topic/b"));
```
