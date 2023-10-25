# Tiedie Python Sample App

Copyright (c) 2023, Cisco Systems, Inc. and/or its affiliates.
All rights reserved.
See accompanying LICENSE file in this distribution

## Configuration

The application can be configured in the [`config/config.ini`](config/config.ini) file. 

The application needs to be configured with the CA certificate used by the gateway.  
If you are using the tiedie gateway included in this repository, you can copy the certificate from `../../gateway/ca_certificates/ca.pem`.

The sample app has an option of authenticating with the gateway using certificates or API keys. 

### Configuring API keys

API keys need to be generated only for the onboarding app. API keys for the control and data receiver applications will be generated automatically using the onboarding app credentials.  

See the gateway [README](../../gateway/README.md#generate-api-keys) for more details on generating an onboarding app API key. 

### Configuring certificates

Optionally, you can also configure the sample app to use certificates. In that case, you will need certificates generated for the onboarding, control and data app separately. 

These certificates can be placed in the `config/` directory and the paths can be configured in the `config/config.ini` file. 

See the gateway [README](../../gateway/README.md#generate-client-private-key-and-certificate) for more details on generating these certificates. 

## Running the App

### Natively

```bash
cd python-sdk

# Optionally, create a virtual env
python3 -m venv venv
source venv/bin/activate

# Install the TieDie python SDK
pip3 install . 

cd sample-python-app

# Install the sample app dependencies
pip3 install -r requirements.txt

python3 src/app.py
```

### Docker

There is a `docker-compose.yaml` file in this directory. This mounts the `config` directory to the root of the container.  
Make sure that the paths in the `config.ini` file are absolute paths (E.g., `CA_PEM_PATH = "/config/ca.pem"`). 

```bash
docker compose up --build
```

