# Copyright (c) 2023, Cisco Systems, Inc. and/or its affiliates.
# All rights reserved.
# See LICENSE file in this distribution.
# SPDX-License-Identifier: Apache-2.0

"""
This module implements FDO dispatch for SCIM.
"""

from models import FDOExtension
from database import session
from tiedie_exceptions import SchemaError,DeviceExists


def fdo_create_device(request,device_id):
    """
    Process SCIM Creation request for an FDO device.  Return an FDOExtension
    """
    fdo_json = request.json.get(
        "urn:ietf:params:scim:schemas:extension:fido-device-onboard:2.0:Device")
    fdo_voucher = fdo_json.get("fdoVoucher",None)

    if not fdo_voucher:
        raise SchemaError("Voucher required")

    if FDOExtension.query.filter_by(device_id=device_id).first():
        raise DeviceExists

# do FDO integration here.

    return FDOExtension(device_id=device_id,fdo_voucher=fdo_voucher)

def fdo_update_device(request):
    """
    update existing entry
    """

    entry: FDOExtension = session.get(FDOExtension, request.json["id"])

    if not entry:
        return fdo_create_device(request,request.json["id"])

    fdo_json = request["urn:ietf:params:scim:schemas:extension:fido-device-onboard:2.0:Device"]

    if not "fdoVoucher" in fdo_json:
        raise SchemaError("There's only one field to update and you didn't update it!")
    entry.fdo_voucher = fdo_json["fdoVoucher"]
    return entry
