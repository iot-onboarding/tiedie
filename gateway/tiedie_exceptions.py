# Copyright (c) 2023, Cisco Systems, Inc. and/or its affiliates.
# All rights reserved.
# See LICENSE file in this distribution.
# SPDX-License-Identifier: Apache-2.0

"""
Exceptions that might be raised in the gateway
"""

class DeviceExists(Exception):
    """
    This is raised when trying to create a device that already exists.
    """

class MABNotSupported(Exception):
    """
    Throw this if MAB is not permitted in this environment.
    """

class FDONotSupported(Exception):
    """
    Throw this if FDO is not permitted in this environment.
    """

class SchemaError(Exception):
    """
    Something is wrong with the request due to a schema error.
    """
