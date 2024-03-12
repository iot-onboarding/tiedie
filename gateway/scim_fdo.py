# Copyright (c) 2023, Cisco Systems, Inc. and/or its affiliates.
# All rights reserved.
# See LICENSE file in this distribution.
# SPDX-License-Identifier: Apache-2.0

"""
This module implements FDO dispatch for SCIM.
"""

import requests
from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, relationship, mapped_column
from scim_extensions import scim_ext_create, scim_ext_update,scim_ext_delete
from models import Device
from database import session,db
from tiedie_exceptions import SchemaError,DeviceExists,FDONotSupported
from config import FDO_SUPPORT, FDO_OWNER_URI,WANT_FDO

class FDOExtension(db.Model):
    """
    Implements Fido Device Onboarding Object
    """
    __tablename__ = "scim_fdo"

    device_id = mapped_column(UUID(as_uuid=True),ForeignKey("devices.device_id"),
                              primary_key=True)
    fdo_voucher = mapped_column(String)
    device: Mapped[Device] = relationship(back_populates="fdo_extension")

    def __init__(self, device_id, fdo_voucher):
        """
        Populate Object with the two required attributes.
        """

        if not WANT_FDO:
            raise FDONotSupported

        self.device_id = device_id
        self.fdo_voucher = fdo_voucher

    def serialize(self):
        """Serialize output"""

        return {
            "urn:ietf:params:scim:schemas:extension:fido-device-onboard:2.0:Device" : {
                "fdoOwnerVoucher" : self.fdo_voucher
            }
        }
    def __repr__(self):
        return f"<id {self.device_id}>"

def to_pem(vraw):
    """convert b64 voucher to PEM"""
    pem = "-----BEGIN OWNERSHIP VOUCHER-----"
    while len(vraw) > 65:
        pem = pem + "\n" + vraw[:65]
        vraw = vraw[65:]
    pem = pem + "\n" + vraw + "\n----- END OWNERSHIP VOUCHER-----\n"
    return pem

def fdo_create_device(schemas, entry, request,device_id,update=False):
    """
    Process SCIM Creation request for an FDO device.  Return an FDOExtension
    """

    fdoschema= \
        'urn:ietf:params:scim:schemas:extension:fido-device-onboard:2.0:Device'
    # schemas is empty on an update.

    if not update:
        if not fdoschema in schemas:
            return
        schemas.remove(fdoschema)

    fdo_json = request.json.get(fdoschema)
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
    entry.fdo_extension =  FDOExtension(device_id=device_id,
                                        fdo_voucher=fdo_voucherb64)

def fdo_update_device(parent,request):
    """
    update existing entry
    """

    schemas=request.json.get("schemas")
    if not schemas:
        raise SchemaError("No schema list")

    fschema = 'urn:ietf:params:scim:schemas:extension:fido-device-onboard:2.0:Device'
    if not fschema in schemas:
        return

    fdo_entry: FDOExtension = session.get(FDOExtension, request.json["id"])

    # if the fdo_entry doesn't exist, that means the update might have
    # added it.  But the parent should still exist, or something REALLY
    # has gone haywire.

    if not fdo_entry:
        fdo_create_device(None, parent, request,
                          request.json["id"],update=True)
        return

    fdo_json = request[fschema]

    if not "fdoOwnerVoucher" in fdo_json:
        raise SchemaError("There's only one field to update and you didn't update it!")
    fdo_entry.fdo_voucher = fdo_json["fdoOwnerVoucher"]

def fdo_delete_device(entry_id):
    """
    Delete database entries and maybe do a RESTful delete as well.
    """

    entry = session.get(FDOExtension,entry_id)
    if not entry:
        return

    session.delete(entry)
    session.commit()

if WANT_FDO:
    scim_ext_create.append(fdo_create_device)
    scim_ext_update.append(fdo_update_device)
    scim_ext_delete.append(fdo_delete_device)
