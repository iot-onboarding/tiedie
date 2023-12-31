# Copyright (c) 2023, Cisco Systems, Inc. and/or its affiliates.
# All rights reserved.
# See LICENSE file in this distribution.
# SPDX-License-Identifier: Apache-2.0

# For more information, please refer to https://aka.ms/vscode-docker-python
FROM python:3.10-slim

EXPOSE 3000

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

ENV DOCKER_BUILD=1

WORKDIR /app

COPY tiedie /app/tiedie
COPY setup.py /app

RUN python -m pip install .

COPY sample-python-app /app/sample-python-app
WORKDIR /app/sample-python-app

RUN python -m pip install -r requirements.txt

CMD gunicorn --worker-class eventlet -w 1 -b 0.0.0.0:3000 --chdir=src app:app
