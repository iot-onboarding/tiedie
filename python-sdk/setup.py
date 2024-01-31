""" Setup file for tiedie SDK for Python. """

# Copyright (c) 2023, Cisco Systems, Inc. and/or its affiliates.
# All rights reserved.
# See LICENSE file in this distribution.
# SPDX-License-Identifier: Apache-2.0

from setuptools import setup, find_packages

setup(
    name='tiedie',
    version='1.0',
    description='Tiedie SDK for Python',
    packages=find_packages(),
    install_requires=[
        'attr',
        'requests',
        'urllib3',
        'paho-mqtt',
        'protobuf',
        'google',
        'cryptography',
        'certifi',
        'pyOpenSSL',
        'pydantic==2.4',
    ],
    extras_require={
        'test': [
            'pytest==7.4',
            'responses==0.24.0',
            'pytest-cov>=4.1'
        ]
    }
)
