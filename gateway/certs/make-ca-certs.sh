#!/bin/sh
# Copyright (c) 2023 Cisco Systems and/or its affiliates
# All Rights Reserved.
# See LICENSE in distribution for licensing information.

# Simple script to generate CA certificates

CACERTDIR=../ca_certificates

if [ -d $CACERTDIR ]; then
    echo "$0: $CACERTDIR directory already exists.  Remove before Running." >&2
    exit -1
fi

mkdir $CACERTDIR

openssl genrsa -out $CACERTDIR/ca.key 4096
openssl req -config tiedie-ca-openssl.cnf -x509 -new -nodes -key $CACERTDIR/ca.key -sha256 -days 365 -out $CACERTDIR/ca.pem -subj "/CN=TieDie Test CA/C=US/O=MyOrg/OU=CA.$$"
