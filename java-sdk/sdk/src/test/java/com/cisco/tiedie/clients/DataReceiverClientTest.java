// Copyright (c) 2023, Cisco and/or its affiliates.
// All rights reserved.
// See license in distribution for details.

package com.cisco.tiedie.clients;

import com.cisco.tiedie.auth.ApiKeyAuthenticator;
import com.cisco.tiedie.auth.CertificateAuthenticator;
import org.eclipse.paho.client.mqttv3.MqttException;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import java.io.InputStream;
import java.security.KeyStore;
import java.util.UUID;

import static org.junit.jupiter.api.Assertions.assertNotNull;

class DataReceiverClientTest {

    private static final String CA_PEM_PATH = "/ca.pem";
    private static final String DATA_APP_ID = "data-app-1";
    private static final String DATA_APP_KEY = UUID.randomUUID().toString();

    private static final String DATA_CERT_PATH = "/data-app.p12";

    @Test
    @DisplayName("Data app with key")
    void dataAppWithKey() throws Exception {
        InputStream caStream = DataReceiverClientTest.class.getResourceAsStream(CA_PEM_PATH);
        String baseUrl = "ssl://localhost:8883";
        var authenticator = ApiKeyAuthenticator.create(caStream, DATA_APP_ID, DATA_APP_KEY);
        var dataReceiverClient = new DataReceiverClient(baseUrl, authenticator);

        assertNotNull(dataReceiverClient);
    }

    @Test
    @DisplayName("Data app with cert")
    void dataAppWithCert() throws Exception {
        try (InputStream caStream = ControlClientTest.class.getResourceAsStream(CA_PEM_PATH);
             InputStream clientKeystoreStream = ControlClientTest.class.getResourceAsStream(DATA_CERT_PATH)) {
            KeyStore keyStore = KeyStore.getInstance("PKCS12");
            keyStore.load(clientKeystoreStream, "".toCharArray());

            CertificateAuthenticator authenticator = CertificateAuthenticator.create(caStream, keyStore, "");
            String baseUrl = "ssl://localhost:8883";

            var dataReceiverClient = new DataReceiverClient(baseUrl, authenticator);

            assertNotNull(dataReceiverClient);
        }
    }

}