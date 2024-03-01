# Copyright (c) 2023, Cisco Systems, Inc. and/or its affiliates.
# All rights reserved.
# See LICENSE file in this distribution.
# SPDX-License-Identifier: Apache-2.0

"""
This module implements Ethernet MAB dispatch for SCIM.
"""

import ciscoisesdk
from ciscoisesdk.exceptions import ApiError
from models import EtherMABExtension
from database import session
from config import ISE_SUPPORT, ISE_HOST, ISE_USERNAME, ISE_PASSWORD
from tiedie_exceptions import SchemaError,DeviceExists,ISEError

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

def ethermab_create_device(request,device_id):
    """
    Process SCIM Creation request for a MAB device.  Return a EtherMABExtension
    """
    mab_json = request.json.get("urn:ietf:params:scim:schemas:extension:ethernet-mab:2.0:Device")
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

    return EtherMABExtension(device_id=device_id,device_mac_address=device_mac_address)

def ethermab_update_device(request):
    """
    update existing entry
    """

    entry: EtherMABExtension = session.get(EtherMABExtension, request.json["id"])

    if not entry:
        return ethermab_create_device(request,request.json["id"])

    mab_json = request["urn:ietf:params:scim:schemas:extension:ethernet-mab:2.0:Device"]

    if not "deviceMacAddress" in mab_json:
        raise SchemaError("There's only one field to update and you didn't update it!")
    mac_addr = mab_json["deviceMacAddress"]
    old_mac = entry.device_mac_address
    entry.device_mac_address = mac_addr
    if not ISE_SUPPORT:
        return entry
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
    return entry

def ethermab_get_filtered_entries(mac_address):
    """ Return Ethernet MAB filtered entries """

    return EtherMABExtension.query.filter_by(device_mac_address=mac_address).all()

def ethermab_delete_device(entry):
    """
    delete from ISE database if necessary
    """

    if not ISE_SUPPORT:
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
