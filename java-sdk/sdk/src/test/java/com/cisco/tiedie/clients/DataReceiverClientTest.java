// Copyright (c) 2023, Cisco and/or its affiliates.
// All rights reserved.
// See LICENSE file in this distribution.
// SPDX-License-Identifier: Apache-2.0

package com.cisco.tiedie.clients;

import com.cisco.tiedie.auth.ApiKeyAuthenticator;
import com.cisco.tiedie.auth.CertificateAuthenticator;
import com.cisco.tiedie.clients.utils.CertificateHelper;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import java.io.InputStream;
import java.security.KeyStore;
import java.security.cert.X509Certificate;
import java.util.UUID;

import static org.junit.jupiter.api.Assertions.assertNotNull;

class DataReceiverClientTest {
    private static final String DATA_APP_ID = "data-app-1";
    private static final String DATA_APP_KEY = UUID.randomUUID().toString();

    InputStream caStream;
    KeyStore keyStore;

    DataReceiverClientTest() throws Exception {
        var rootCertSubject = CertificateHelper.createX500Name("ca");
        var rootKeyPair = CertificateHelper.createKeyPair();
        var rootCert = CertificateHelper.createCaCertificate(rootKeyPair, rootCertSubject);

        var appKeyPair = CertificateHelper.createKeyPair();
        X509Certificate appCert = CertificateHelper.createAppCertificate(appKeyPair, DATA_APP_ID, rootKeyPair,
        rootCertSubject);
        
        caStream = CertificateHelper.createPemInputStream(rootCert);
        keyStore = CertificateHelper.createKeyStore(appKeyPair, appCert, DATA_APP_ID);
    }

    @Test
    @DisplayName("Data app with key")
    void dataAppWithKey() throws Exception {
        String baseUrl = "ssl://localhost:8883";
        var authenticator = ApiKeyAuthenticator.create(caStream, DATA_APP_ID, DATA_APP_KEY);
        var dataReceiverClient = new DataReceiverClient(baseUrl, authenticator);

        assertNotNull(dataReceiverClient);
    }

    @Test
    @DisplayName("Data app with cert")
    void dataAppWithCert() throws Exception {
        CertificateAuthenticator authenticator = CertificateAuthenticator.create(caStream, keyStore, "");
        String baseUrl = "ssl://localhost:8883";

        var dataReceiverClient = new DataReceiverClient(baseUrl, authenticator);

        assertNotNull(dataReceiverClient);
    }

}