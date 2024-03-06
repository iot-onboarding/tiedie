# Copyright (c) 2023, Cisco Systems, Inc. and/or its affiliates.
# All rights reserved.
# See LICENSE file in this distribution.
# SPDX-License-Identifier: Apache-2.0

"""
This module implements FDO dispatch for SCIM.
"""

import requests
from models import FDOExtension
from database import session
from tiedie_exceptions import SchemaError,DeviceExists,FDONotSupported
from config import FDO_SUPPORT, FDO_OWNER_URI,WANT_FDO

def to_pem(vraw):
    """convert b64 voucher to PEM"""
    pem = "-----BEGIN OWNERSHIP VOUCHER-----"
    while len(vraw) > 65:
        pem = pem + "\n" + vraw[:65]
        vraw = vraw[65:]
    pem = pem + "\n" + vraw + "\n----- END OWNERSHIP VOUCHER-----\n"
    return pem

def fdo_create_device(request,device_id):
    """
    Process SCIM Creation request for an FDO device.  Return an FDOExtension
    """

    if not WANT_FDO:
        raise FDONotSupported

    fdo_json = request.json.get(
        "urn:ietf:params:scim:schemas:extension:fido-device-onboard:2.0:Device")
    fdo_voucherb64 = fdo_json.get("fdoOwnerVoucher",None)

    if not fdo_voucherb64:
        raise SchemaError("fdoOwnerVoucher required")

    fdo_voucher=to_pem(fdo_voucherb64)

    if FDOExtension.query.filter_by(device_id=device_id).first():
        raise DeviceExists

    if FDO_SUPPORT:
        try:
            res=requests.post(url=FDO_OWNER_URI,data=fdo_voucher,
                              headers={'Content-Type':
                                       'text/plain'},
                              timeout=5)
        except Exception as e:
            raise FDONotSupported(str(e)) from e
        if res.status_code not in (200,201):
            raise FDONotSupported(res.text)
    return FDOExtension(device_id=device_id,fdo_voucher=fdo_voucherb64)

def fdo_update_device(request):
    """
    update existing entry
    """

    entry: FDOExtension = session.get(FDOExtension, request.json["id"])

    if not entry:
        return fdo_create_device(request,request.json["id"])

    fdo_json = request["urn:ietf:params:scim:schemas:extension:fido-device-onboard:2.0:Device"]

    if not "fdoOwnerVoucher" in fdo_json:
        raise SchemaError("There's only one field to update and you didn't update it!")
    entry.fdo_voucher = fdo_json["fdoOwnerVoucher"]
    return entry
