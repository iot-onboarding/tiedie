<!--
Copyright (c) 2023, Cisco Systems, Inc. and/or its affiliates.
All rights reserved.
See LICENSE file in this distribution.
SPDX-License-Identifier: Apache-2.0
-->

# Tiedie Python Sample App

Copyright (c) 2023, Cisco Systems, Inc. and/or its affiliates.
All rights reserved.
See accompanying LICENSE file in this distribution

## Configuration

The application can be configured in the [`config/config.ini`](config/config.ini) file.

The application needs to be configured with the CA certificate used by the gateway.  
If you are using the tiedie gateway included in this repository, you can copy the certificate from `../../gateway/ca_certificates/ca.pem` to `./config/ca.pem`.

The sample app has an option of authenticating with the gateway using API keys, certificates, or OAuth2.

### Configuring API keys

API keys need to be generated only for the onboarding app. API keys for the control and data receiver applications will be generated automatically using the onboarding app credentials.

Set `ONBOARDING_APP_API_KEY` in `config/config.ini`.

See the gateway [README](../../gateway/README.md#generate-api-keys) for more details on generating an onboarding app API key.

### Configuring certificates

Optionally, you can also configure the sample app to use certificates. In that case, you will need certificates generated for the onboarding, control and data app separately.

These certificates can be placed in the `config/` directory and the paths can be configured in the `config/config.ini` file:

- `ONBOARDING_APP_CERT_PATH` and `ONBOARDING_APP_KEY_PATH`
- `CONTROL_APP_CERT_PATH` and `CONTROL_APP_KEY_PATH`

See the gateway [README](../../gateway/README.md#generate-client-private-key-and-certificate) for more details on generating these certificates.

### Configuring OAuth2

To enable OAuth2 in the sample app, set the following keys in `config/config.ini`:

- `OAUTH_CLIENT_ID`
- `OAUTH_CLIENT_SECRET`
- `OAUTH_AUTH_ENDPOINT`
- `OAUTH_TOKEN_ENDPOINT`
- `OAUTH_REDIRECT_URI`
- `OAUTH_SCOPES`

When `OAUTH_CLIENT_ID` is set, the app uses OAuth2 for onboarding and control clients.

OAuth2 flow in the app:

1. Requests are redirected to `/oauth2/authorize`.
2. After sign-in, the OAuth provider redirects to `/oauth_callback`.
3. The app sets OAuth session auth from the callback and continues with OAuth-backed requests.

### Other configuration options

The following options are also used by the sample app:

- `CLIENT_CA_PATH`, `ONBOARDING_APP_BASE_URL`, `ONBOARDING_APP_ID`
- `CONTROL_APP_BASE_URL`, `CONTROL_APP_ID`
- `DATA_APP_HOST`, `DATA_APP_PORT`, `DATA_APP_ID`
- `DATA_APP_TLS_ENABLED`, `DATA_APP_TLS_SELF_SIGNED`
- `DATA_APP_MQTT_TYPE` (`client` or `broker`)
- If `DATA_APP_MQTT_TYPE = "broker"`: `DATA_APP_USERNAME`, `DATA_APP_PASSWORD`, `DATA_APP_CA_CERT_PATH`

## Running the App

### Natively

```bash
cd python-sdk

# Optionally, create a virtual env
python3 -m venv venv
source venv/bin/activate

# Install the TieDie python SDK
python -m pip install .

cd sample-python-app

# Install the sample app dependencies
python -m pip install -r requirements.txt

cd src
python app.py
```

### Docker

There is a `docker-compose.yaml` file in the `python-sdk` directory. This mounts the `sample-python-app/config` directory to the root of the container.

Make sure that the paths in the `config.ini` file are container paths (E.g., `CLIENT_CA_PATH = "/config/ca.pem"`).

```bash
cd python-sdk
docker compose up --build
```
