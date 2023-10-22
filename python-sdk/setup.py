#!python
# Copyright (c) 2023, Cisco Systems, Inc. and/or its affiliates.
# All rights reserved.
# See accompanying LICENSE file in this distribution.

from setuptools import setup, find_packages

setup(
    name='tiedie',
    version='1.0',
    description='Tiedie SDK for Python',
    packages=find_packages(),
    install_requires=[
         'attr', 'requests', 'urllib3', 'paho-mqtt', 'protobuf', 'protobuf', 'google', 'cryptography', 'certifi', 'pyOpenSSL'
    ],
)
