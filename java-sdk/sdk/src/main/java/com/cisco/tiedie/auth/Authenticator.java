// Copyright (c) 2023, Cisco and/or its affiliates.
// All rights reserved.
// See LICENSE file in this distribution.
// SPDX-License-Identifier: Apache-2.0

package com.cisco.tiedie.auth;

import okhttp3.OkHttpClient;
import org.eclipse.paho.client.mqttv3.MqttConnectOptions;

import javax.net.ssl.KeyManager;
import javax.net.ssl.KeyManagerFactory;
import javax.net.ssl.TrustManager;
import javax.net.ssl.TrustManagerFactory;
import java.io.InputStream;
import java.security.KeyStore;
import java.security.cert.CertificateFactory;
import java.security.cert.X509Certificate;

/**
 * Interface to support different authentication methods.
 */
public interface Authenticator {
    /**
     * Flag to skip hostname verification.
     * <p>
     * TODO: Handle this differently.
     */
    boolean SKIP_HOSTNAME_VERIFICATION = true;

    /**
     * Get {@link KeyManager} associated with a {@link KeyStore}.
     *
     * @param keyStore {@link KeyStore} object that has the certificate and private key to be used by the client.
     * @param password Password for the {@link KeyStore} object.
     * @return Array of {@link KeyManager} objects. Only the first one is used.
     */
    static KeyManager[] getKeyManagers(KeyStore keyStore, String password) {
        try {
            char[] pwd = password != null ? password.toCharArray() : null;
            KeyManagerFactory keyManagerFactory = KeyManagerFactory.getInstance(KeyManagerFactory.getDefaultAlgorithm());
            keyManagerFactory.init(keyStore, pwd);

            return keyManagerFactory.getKeyManagers();
        } catch (Exception e) {
            throw new RuntimeException(e);
        }
    }

    /**
     * Get {@link TrustManager} that represents the Certificate Authority to verify the server certificate.
     *
     * @param inputStream {@link InputStream} that has the contents of the CA file in PEM format.
     * @return Array of {@link TrustManager} objects. Only the first one is used.
     */
    static TrustManager[] getCaTrustManagers(InputStream inputStream) {
        try {
            CertificateFactory certificateFactory = CertificateFactory.getInstance("X.509");
            X509Certificate caCert = (X509Certificate) certificateFactory.generateCertificate(inputStream);

            KeyStore trustedStore = KeyStore.getInstance(KeyStore.getDefaultType());
            trustedStore.load(null);
            trustedStore.setCertificateEntry(caCert.getSubjectX500Principal().getName(), caCert);
            TrustManagerFactory trustManagerFactory = TrustManagerFactory.getInstance(TrustManagerFactory.getDefaultAlgorithm());
            trustManagerFactory.init(trustedStore);

            return trustManagerFactory.getTrustManagers();
        } catch (Exception e) {
            throw new RuntimeException(e);
        }
    }

    /**
     * @return Returns the ID of the client.
     */
    String getClientID();

    /**
     * @param builder {@link OkHttpClient.Builder} object.
     * @return Updated builder object after adding authentication related settings.
     */
    OkHttpClient.Builder setAuthOptions(OkHttpClient.Builder builder);

    /**
     * Set auth options for the data receiver app.
     * @param mqttConnectOptions {@link MqttConnectOptions} object.
     */
    void setAuthOptions(MqttConnectOptions mqttConnectOptions);
}
