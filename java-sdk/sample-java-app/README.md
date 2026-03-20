<!--
Copyright (c) 2023, Cisco Systems, Inc. and/or its affiliates.
All rights reserved.
See LICENSE file in this distribution.
SPDX-License-Identifier: Apache-2.0
-->

# Getting Started

This is an example of how the TieDie Java SDK can be used to develop an application. 

The sample application can be run as a docker image or natively. 

## Configuration

The application can be configured using one of the following `application.properties` files:

1. `src/main/resources/application.properties` (default if `--spring.config.location` is not provided)
2. `config/application.properties` (used in the run commands below)

For details on how to configure these properties, see [here](src/main/resources/META-INF/additional-spring-configuration-metadata.json).

The application needs to be configured with the CA certificate used by the gateway.
If you are using the tiedie gateway included in this repository, you can copy the certificate from `../../gateway/ca_certificates/ca.pem`.

The sample app has an option of authenticating with the gateway using API keys, certificates, or OAuth2.

### Configuring API keys

API keys need to be generated only for the onboarding app. API keys for the control and data receiver applications are generated automatically using the onboarding app credentials.

See the gateway [README](../../gateway/README.md#generate-api-keys) for more details on generating an onboarding app API key.

### Configuring certificates

Optionally, you can also configure the sample app to use certificates. In that case, you will need certificates generated for the onboarding, control and data app separately.

These certificates can be placed in the `config/` directory and the paths can be configured in either `config/application.properties` or `src/main/resources/application.properties`.

See the gateway [README](../../gateway/README.md#generate-client-private-key-and-certificate) for more details on generating these certificates.

### Configuring OAuth2

To configure OAuth2 in the sample app, set these keys:

```properties
oauth.client-id=
oauth.client-secret=
oauth.auth-endpoint=
oauth.token-endpoint=
oauth.redirect-uri=
oauth.scopes=
```

OAuth flow is enabled when `oauth.client-id`, `oauth.client-secret`, `oauth.auth-endpoint`, `oauth.token-endpoint`, and `oauth.redirect-uri` are set.
When OAuth is enabled, the app redirects requests to `/oauth2/authorize` until an OAuth token is available.
After the user authorizes access, the OAuth provider redirects back to `/oauth_callback`.
The app exchanges the authorization code for a token and then uses that token for TieDie calls.

## Running the sample application

### Natively

From `java-sdk/sample-java-app/`, build the sample app using the following command:

```bash
./gradlew bootJar

java -jar build/libs/tiedie-sample-app-0.0.1-SNAPSHOT.jar --spring.config.location=config/application.properties
```

If `--spring.config.location` is not provided, the default configuration file at `src/main/resources/application.properties` is used.

### Docker

There is a `docker-compose.yaml` file in the `java-sdk/` directory. This mounts the `sample-java-app/config` directory to `/config` in the container.
The checked-in `config/application.properties` works for this flow.

```bash
# from java-sdk/
docker compose up --build
```
