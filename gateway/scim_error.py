# Copyright (c) 2023, Cisco Systems, Inc. and/or its affiliates.
# All rights reserved.
# See LICENSE file in this distribution.
# SPDX-License-Identifier: Apache-2.0

"""

Simple error formating routine for scim.

"""

from flask import jsonify,make_response

def blow_an_error(e,code,scim_code = "invalidSyntax"):
    """
    Simple formating handling routine"
    """

    return make_response(
        jsonify(
            {
                "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Error"],
                "scimType": scim_code,
                "detail": e,
                "status": code,
                }
        ),
        code,
    )
