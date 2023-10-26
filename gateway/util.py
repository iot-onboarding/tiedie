""" Utility module """

# Copyright (c) 2023, Cisco and/or its affiliates.
# All rights reserved.
# See license in distribution for details.

from base64 import b64encode
from os import urandom
import hashlib

SALT_LENGTH = 16
HASH_FUNCTION = 'sha512'
COST_FACTOR = 100000


def make_hash(pwd: str):
    """ Hashes a password with PBKDF2 and returns a formatted hash. """
    password = pwd.encode('utf-8')
    salt = b64encode(urandom(SALT_LENGTH))
    hash_key = b64encode(hashlib.pbkdf2_hmac(
        HASH_FUNCTION, password, salt, COST_FACTOR))
    return f"PBKDF2${HASH_FUNCTION}${COST_FACTOR}${str(salt, 'utf-8')}${str(hash_key, 'utf-8')}"
