# Copyright (c) 2023, Cisco Systems, Inc. and/or its affiliates.
# All rights reserved.
# See LICENSE file in this distribution.
# SPDX-License-Identifier: Apache-2.0

"""

Configures Flask with SQLAlchemy for database
perations and initializes a session.

"""

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import Session

db = SQLAlchemy()
session: Session = db.session
