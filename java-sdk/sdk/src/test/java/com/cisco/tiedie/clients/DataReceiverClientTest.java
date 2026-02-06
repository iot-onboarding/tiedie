// Copyright (c) 2023, Cisco Systems, Inc. and/or its affiliates.
// All rights reserved.
// See LICENSE file in this distribution.
// SPDX-License-Identifier: Apache-2.0

package com.cisco.tiedie.clients;

import com.cisco.tiedie.auth.ApiKeyAuthenticator;
import com.cisco.tiedie.auth.CertificateAuthenticator;
import com.cisco.tiedie.clients.utils.CertificateHelper;
import com.cisco.tiedie.dto.telemetry.DataSubscription;
import com.cisco.tiedie.utils.ObjectMapperSingleton;

import org.eclipse.paho.client.mqttv3.MqttConnectOptions;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import java.io.InputStream;
import java.lang.reflect.Field;
import java.lang.reflect.Method;
import java.security.KeyStore;
import java.security.cert.X509Certificate;
import java.util.List;
import java.util.UUID;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNull;

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
        assertFalse(dataReceiverClient.isConnected());
        dataReceiverClient.unsubscribe("data-app/example/#");
        dataReceiverClient.unsubscribe(java.util.List.of("data-app/example/#", "data-app/other/#"));
        dataReceiverClient.disconnect();
    }

    @Test
    @DisplayName("Data app with cert")
    void dataAppWithCert() throws Exception {
        CertificateAuthenticator authenticator = CertificateAuthenticator.create(caStream, keyStore, "");
        String baseUrl = "ssl://localhost:8883";

        var dataReceiverClient = new DataReceiverClient(baseUrl, authenticator);

        assertNotNull(dataReceiverClient);
    }

    @Test
    @DisplayName("TCP broker URL clears SSL socket factory")
    void tcpBrokerUrlClearsSslSocketFactory() throws Exception {
        String baseUrl = "tcp://localhost:1883";
        var authenticator = ApiKeyAuthenticator.create(caStream, DATA_APP_ID, DATA_APP_KEY);
        var dataReceiverClient = new DataReceiverClient(baseUrl, authenticator);

        Field connectOptionsField = DataReceiverClient.class.getDeclaredField("mqttConnectOptions");
        connectOptionsField.setAccessible(true);
        MqttConnectOptions connectOptions = (MqttConnectOptions) connectOptionsField.get(dataReceiverClient);

        assertNotNull(connectOptions);
        assertNull(connectOptions.getSocketFactory());
    }

    @Test
    @DisplayName("Decode single subscription payload")
    void decodeSingleSubscriptionPayload() throws Exception {
        var authenticator = ApiKeyAuthenticator.create(caStream, DATA_APP_ID, DATA_APP_KEY);
        var dataReceiverClient = new DataReceiverClient("tcp://localhost:1883", authenticator);

        DataSubscription subscription = new DataSubscription();
        subscription.setDeviceID("device-1");
        subscription.setData(new byte[]{0x01, 0x02});

        byte[] payload = ObjectMapperSingleton.getCborInstance().writeValueAsBytes(subscription);
        List<DataSubscription> decoded = decodePayload(dataReceiverClient, payload);

        assertEquals(1, decoded.size());
        assertEquals("device-1", decoded.get(0).getDeviceID());
    }

    @Test
    @DisplayName("Decode array subscription payload")
    void decodeArraySubscriptionPayload() throws Exception {
        var authenticator = ApiKeyAuthenticator.create(caStream, DATA_APP_ID, DATA_APP_KEY);
        var dataReceiverClient = new DataReceiverClient("tcp://localhost:1883", authenticator);

        DataSubscription first = new DataSubscription();
        first.setDeviceID("device-1");
        first.setData(new byte[]{0x01});

        DataSubscription second = new DataSubscription();
        second.setDeviceID("device-2");
        second.setData(new byte[]{0x02});

        byte[] payload = ObjectMapperSingleton.getCborInstance().writeValueAsBytes(List.of(first, second));
        List<DataSubscription> decoded = decodePayload(dataReceiverClient, payload);

        assertEquals(2, decoded.size());
        assertEquals("device-1", decoded.get(0).getDeviceID());
        assertEquals("device-2", decoded.get(1).getDeviceID());
    }

    @SuppressWarnings("unchecked")
    private static List<DataSubscription> decodePayload(DataReceiverClient client, byte[] payload) throws Exception {
        Method decodeMethod = DataReceiverClient.class.getDeclaredMethod("decodeDataSubscriptions", byte[].class);
        decodeMethod.setAccessible(true);
        return (List<DataSubscription>) decodeMethod.invoke(client, payload);
    }

}
