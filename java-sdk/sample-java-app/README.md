<!--
Copyright (c) 2023, Cisco and/or its affiliates.
All rights reserved.
See LICENSE file in this distribution.
SPDX-License-Identifier: Apache-2.0
-->

# Getting Started

This is an example of how the TieDie Java SDK can be used to develop an application. 

The sample application can be run as a docker image or natively. 

## Configuration

The application can be configured in the `application.properties` file.  
For details on how to configure this file, see [here](src/main/resources/META-INF/additional-spring-configuration-metadata.json).

The application needs to be configured with the CA certificate used by the gateway.  
If you are using the tiedie gateway included in this repository, you can copy the certificate from `../../gateway/ca_certificates/ca.pem`.

The sample app has an option of authenticating with the gateway using certificates or API keys. 

### Configuring API keys

API keys need to be generated only for the onboarding app. API keys for the control and data receiver applications will be generated automatically using the onboarding app credentials.  

See the gateway [README](../../gateway/README.md#generate-api-keys) for more details on generating an onboarding app API key. 

### Configuring certificates

Optionally, you can also configure the sample app to use certificates. In that case, you will need certificates generated for the onboarding, control and data app separately. 

These certificates can be placed in the `config/` directory and the paths can be configured in the `config/application.properties` file. 

See the gateway [README](../../gateway/README.md#generate-client-private-key-and-certificate) for more details on generating these certificates. 

## Running the sample application

### Natively

Build the sample app using the following command:

```bash
./gradlew bootJar

java -jar build/libs/tiedie-sample-app-0.0.1-SNAPSHOT.jar --spring.config.location=config/application.properties
```

If `--spring.config.location` is not provided, the default configuration file at `src/main/resources/application.properties`.

### Docker

There is a `docker-compose.yaml` file in this directory. This mounts the `config` directory to the root of the container.  
Make sure that the paths in the `application.properties` file are absolute paths (E.g., `client.ca_path=/config/ca.pem`). 

```bash
# build the jar like before
./gradlew bootJar

docker compose up
```
