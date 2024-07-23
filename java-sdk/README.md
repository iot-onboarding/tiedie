<!--
Copyright (c) 2023, Cisco Systems, Inc. and/or its affiliates.
All rights reserved.
See LICENSE file in this distribution.
SPDX-License-Identifier: Apache-2.0
-->

# TieDie SDK for Java

This SDK is used to access IOT devices via the virtualized interfaces
for BLE.  A sample application making use of the SDK can be found in
./sample-java-sdk.

## Prerequisites

For the Java SDK, Java version 11 or greater or openjdk version 11 to 18 should be used.

## Build 

All instructions for building the SDK take place in the SDK directory.

```bash
cd ./sdk
```

Build the JAR using the following command: 

```bash
./gradlew build
```

You can find the SDK JAR at `build/libs/tiedie-sdk-java-1.0.jar`.

## Usage

### Authentication

There are two methods of authentication with TieDie.

1. API key based
2. Certificate based

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

Authenticator authenticator = CertificateAuthenticator.create(inputStream, keyStore, "password");
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

var authenticator = ApiKeyAuthenticator.create(caStream, dataAppId, endpointApp.getClientToken());
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
            new EndpointAppsExtension(List.of(endpointApp1, endpointApp2))
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
ControlClient controlClient = new ControlClient("https://<host>/control", authenticator);
```

You can control a device using the APIs using the corresponding `Device` object.

#### Connect

```java
TiedieResponse<List<DataParameter>> response = controlClient.connect(device);
```

#### Disconnect

```java
TiedieResponse<Void> response = controlClient.disconnect(device);
```

#### Read

```java
var dataParameter = new BleDataParameter(deviceId, serviceUUID, charUUID);
// ... or ...
var dataParameter = new ZigbeeDataParameter(deviceId, endpointID, clusterID, attributeID, type);

TiedieResponse<DataResponse> response = controlClient.read(dataParameter);
```

#### Write

```java
TiedieResponse<DataResponse> response = controlClient.write(dataParameter);
```

#### Subscribe

```java
TiedieResponse<Void> subscribe = controlClient.subscribe(dataParameter);
```

#### Register Topic

To register a topic on a GATT subscription:

```java
TiedieResponse<Void> topicResponse = controlClient.registerTopic(topic, 
        DataRegistrationOptions.builder()
                .dataFormat(DataFormat.DEFAULT)
                .dataParameter(dataParameter)
                .build());
```

To register a topic on advertisements:

```java
TiedieResponse<Void> topicResponse = controlClient.registerTopic(topic,
        AdvertisementRegistrationOptions.builder()
                .dataFormat(DataFormat.DEFAULT)
                .advertisementFilterType(BleAdvertisementFilterType.DENY)
                .advertisementFilters(List.of(
                        new BleAdvertisementFilter("*", "ff", "4c00*"),
                        new BleAdvertisementFilter("*", "01", "1a")
                ))
                .build());
```

To register a topic on connection status: 

```java
TiedieResponse<Void> topicResponse = controlClient.registerTopic(topic, 
        ConnectionRegistrationOptions.builder()
                .dataFormat(DataFormat.DEFAULT)
                .devices(List.of(response.getBody()))
                .build());
```

#### Register Data App

```java
TiedieResponse<Void> dataAppResponse = controlClient.registerDataApp("data-app", topic);
```

#### Un-register Data App

```java
TiedieResponse<Void> response = controlClient.unregisterTopic(topic, deviceIds);
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
