# Copyright (c) 2023, Cisco Systems, Inc. and/or its affiliates.
# All rights reserved.
# See LICENSE file in this distribution.
# SPDX-License-Identifier: Apache-2.0

"""
Flask application factory
"""

from typing import Optional

from flask import Flask
from flask_migrate import Migrate
from scim import scim_app
from control import control_app
from database import db
from config import WANT_ETHER_MAB, WANT_FDO
from scim_extensions import reset_scim_extensions
from scim_ble import register_ble_extension
from scim_ethermab import register_ethermab_extension
from scim_fdo import register_fdo_extension

migrate = Migrate()

def create_app(url: str,
               want_ether_mab: Optional[bool] = None,
               want_fdo: Optional[bool] = None):
    """ Create Flask Application """
    app = Flask(__name__)

    app.config["SQLALCHEMY_DATABASE_URI"] = url
    app.config['JSON_SORT_KEYS'] = False

    if want_ether_mab is None:
        want_ether_mab = bool(WANT_ETHER_MAB)
    if want_fdo is None:
        want_fdo = bool(WANT_FDO)

    reset_scim_extensions()
    register_ble_extension()
    register_ethermab_extension(want_ether_mab)
    register_fdo_extension(want_fdo)

    migrate.init_app(app, db)
    db.init_app(app)
    app.url_map.strict_slashes = False

    app.register_blueprint(control_app)
    app.register_blueprint(scim_app)

    return app
