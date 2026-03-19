# Copyright (c) 2024, Cisco Systems, Inc. and/or its affiliates.
# All rights reserved.
# See LICENSE file in this distribution.
# SPDX-License-Identifier: Apache-2.0

"""

This module implements SCIM extensions in a generic fashion.

"""

scim_ext_create = []
scim_ext_read = []
scim_ext_update = []
scim_ext_delete = []


def reset_scim_extensions():
    """Reset all registered SCIM extension hooks."""
    scim_ext_create.clear()
    scim_ext_read.clear()
    scim_ext_update.clear()
    scim_ext_delete.clear()


def _append_unique(target, fn):
    if fn not in target:
        target.append(fn)


def register_scim_extension(create_fn, read_fn, update_fn, delete_fn):
    """Register extension hooks without creating duplicate entries."""
    _append_unique(scim_ext_create, create_fn)
    _append_unique(scim_ext_read, read_fn)
    _append_unique(scim_ext_update, update_fn)
    _append_unique(scim_ext_delete, delete_fn)
