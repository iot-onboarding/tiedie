# Copyright (c) 2023, Cisco Systems, Inc. and/or its affiliates.
# All rights reserved.
# See LICENSE file in this distribution.
# SPDX-License-Identifier: Apache-2.0

"""
This module implements Ethernet MAB dispatch for SCIM.
"""

import ciscoisesdk
from ciscoisesdk.exceptions import ApiError
from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, relationship, mapped_column
from scim_extensions import scim_ext_create, scim_ext_update, scim_ext_delete
from models import Device
from database import session,db
from config import ISE_SUPPORT, ISE_HOST, ISE_USERNAME, ISE_PASSWORD, \
    WANT_ETHER_MAB
from tiedie_exceptions import SchemaError, DeviceExists, ISEError, \
    MABNotSupported

class EtherMABExtension(db.Model):
    """
    MAC Authenticated Bypass Extension.  Use this for 802.3 devices that
    support no other form of authentication.  Yes, Yuck.
    """
    __tablename__ = "ethernetmab"

    device_id = mapped_column(UUID(as_uuid=True),ForeignKey("devices.device_id"),
                              primary_key=True)
    device_mac_address = mapped_column(String)
    device: Mapped[Device] = relationship(back_populates="ethermab_extension")

    def __init__(
	self,
        device_id,
        device_mac_address):
        """
        Populate Object with the two required attributes.
        """

        if not WANT_ETHER_MAB:
            raise MABNotSupported

        self.device_id = device_id
        self.device_mac_address = device_mac_address

    def serialize(self):
        """Serialize output"""

        return {
            "urn:ietf:params:scim:schemas:extension:ethernet-mab:2.0:Device" : {
                "deviceMacAddress" : self.device_mac_address
            }
        }
    def __repr__(self):
        return f"<id {self.device_id}>"

def init_ise():
    """
    This sets up the ERS API.  Goes to the environment for inputs.
    """

    if not ISE_SUPPORT:
        return False

    ui_url = 'https://' + ISE_HOST
    mnt_url = ui_url
    ers_url = ui_url + ':9060'
    px_url = ui_url + ':8910'

    try:
        api=ciscoisesdk.IdentityServicesEngineAPI(username=ISE_USERNAME,
                                                  password=ISE_PASSWORD,
                                                  uses_api_gateway=False,
                                                  ers_base_url=ers_url,
                                                  version="3.1.0",
                                                  ui_base_url=ui_url,
                                                  mnt_base_url=mnt_url,
                                                  uses_csrf_token=False,
                                                  px_grid_base_url=px_url,
                                                  verify=False)
        return api
    except ApiError as e:
        raise ISEError(e.description) from e

def ethermab_create_device(schemas,entry,request,device_id,update=False):
    """
    Process SCIM Creation request for a MAB device.  Return a EtherMABExtension
    """

    ethschema='urn:ietf:params:scim:schemas:extension:ethernet-mab:2.0:Device'

    if not update:
        if not ethschema in schemas:
            return
        schemas.remove(ethschema)

    mab_json = request.json.get(ethschema)
    device_mac_address = mab_json.get("deviceMacAddress",None)
    if not device_mac_address:
        raise SchemaError("MAC address required")

    if EtherMABExtension.query.filter_by(device_mac_address=device_mac_address).first():
        raise DeviceExists

    api=init_ise()
    endpoint=None
    if api:
        try:
            endpoint = api.endpoint.get_endpoint_by_name(device_mac_address)
        except ApiError as e:
            if e.status_code != 404:
                raise ISEError(e.description) from e
            # if it is a 404, device is in ISE- let it be
        try:
            if not endpoint:
                api.endpoint.create_endpoint(mac=device_mac_address)
        except ApiError as e:
            raise ISEError(e.description) from e
    entry.ethermab_extension = EtherMABExtension(
        device_id=device_id,device_mac_address=device_mac_address)


def ethermab_update_device(parent,request):
    """
    update existing entry
    """

    schemas=request.json.get("schemas")
    if not schemas:
        raise SchemaError("No schema list")

    ethschema = 'urn:ietf:params:scim:schemas:extension:ethernet-mab:2.0:Device'
    if not ethschema in schemas:
        return

    ether_entry: EtherMABExtension = session.get(EtherMABExtension, request.json["id"])

    if not ether_entry:
        ethermab_create_device(None, parent, request,
                               request.json["id"],update=True)
        return

    mab_json = request[ethschema]

    if not "deviceMacAddress" in mab_json:
        raise SchemaError("There's only one field to update and you didn't update it!")
    mac_addr = mab_json["deviceMacAddress"]
    old_mac = ether_entry.device_mac_address
    ether_entry.device_mac_address = mac_addr
    if not ISE_SUPPORT:
        return
    api=init_ise()
    endpoint = None
    if api:
        try:
            endpoint = api.endpoint.get_endpoint_by_name(old_mac)
        except ApiError as e:
            if e.status_code != 404:
                raise ISEError(e.description) from e
        if endpoint:
            endpoint_id = endpoint.response.ERSEndPoint['id']
            try:
                api.endpoint.create_endpoint(mac=mac_addr)
                api.endpoint.delete_endpoint_by_id(endpoint_id)
            except ApiError as e:
                raise ISEError(e.description) from e

def ethermab_get_filtered_entries(mac_address):
    """ Return Ethernet MAB filtered entries """

    return EtherMABExtension.query.filter_by(device_mac_address=mac_address).all()

def ethermab_delete_device(entry_id):
    """
    delete from ISE database if necessary
    """

    entry = session.get(EtherMABExtension,entry_id)
    if not entry:
        return

    api=init_ise()
    if api:
        try:
            endpoint = api.endpoint.get_endpoint_by_name(entry.device_mac_address)
        except ApiError as e:
            if e.status_code != 404:
                raise ISEError(e.description) from e
        if endpoint:
            endpoint_id = endpoint.response.ERSEndPoint['id']
            try:
                api.endpoint.delete_endpoint_by_id(endpoint_id)
            except ApiError as e:
                raise ISEError(e.description) from e
    session.delete(entry)
    session.commit()



if WANT_ETHER_MAB:
    scim_ext_create.append(ethermab_create_device)
    scim_ext_update.append(ethermab_update_device)
    scim_ext_delete.append(ethermab_delete_device)
