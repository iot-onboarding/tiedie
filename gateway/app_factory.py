# Copyright (c) 2023, Cisco Systems, Inc. and/or its affiliates.
# All rights reserved.
# See LICENSE file in this distribution.
# SPDX-License-Identifier: Apache-2.0

"""
Flask application factory
"""

from flask import Flask
from flask_migrate import Migrate
from scim import scim_app
from control import control_app
from database import db

migrate = Migrate()

def create_app(url: str):
    """ Create Flask Application """
    app = Flask(__name__)

    app.config["SQLALCHEMY_DATABASE_URI"] = url
    app.config['JSON_SORT_KEYS'] = False

    migrate.init_app(app, db)
    db.init_app(app)
    app.url_map.strict_slashes = False

    app.register_blueprint(control_app)
    app.register_blueprint(scim_app)

    return app
