// Copyright (c) 2023, Cisco Systems, Inc. and/or its affiliates.
// All rights reserved.
// See LICENSE file in this distribution.
// SPDX-License-Identifier: Apache-2.0

package com.cisco.tiedie.auth;

import lombok.AccessLevel;
import lombok.AllArgsConstructor;
import okhttp3.OkHttpClient;
import org.eclipse.paho.client.mqttv3.MqttConnectOptions;

import javax.net.ssl.SSLContext;
import javax.net.ssl.TrustManager;
import javax.net.ssl.X509TrustManager;
import java.io.InputStream;
import java.util.function.Supplier;

/**
 * Client authentication method using OAuth2 bearer tokens.
 */
@AllArgsConstructor(access = AccessLevel.PRIVATE)
public class OAuth2Authenticator implements Authenticator {
    private static final String AUTHORIZATION_HEADER = "Authorization";

    private final String clientId;
    private final Supplier<String> accessTokenSupplier;
    private final TrustManager[] trustManagers;

    /**
     * Create a new {@link OAuth2Authenticator} object.
     *
     * @param caInputStream       {@link InputStream} with the CA file in PEM format.
     * @param clientId            OAuth client identifier to use as client identity.
     * @param accessTokenSupplier Supplier that returns a current OAuth bearer token.
     * @return Authenticator object that can be passed to a client.
     */
    public static OAuth2Authenticator create(
            InputStream caInputStream,
            String clientId,
            Supplier<String> accessTokenSupplier
    ) {
        var trustManagers = Authenticator.getCaTrustManagers(caInputStream);
        return new OAuth2Authenticator(clientId, accessTokenSupplier, trustManagers);
    }

    /**
     * Create a new {@link OAuth2Authenticator} object that uses the JVM default
     * trust store for HTTPS requests.
     *
     * @param clientId            OAuth client identifier to use as client identity.
     * @param accessTokenSupplier Supplier that returns a current OAuth bearer token.
     * @return Authenticator object that can be passed to a client.
     */
    public static OAuth2Authenticator create(
            String clientId,
            Supplier<String> accessTokenSupplier
    ) {
        return new OAuth2Authenticator(clientId, accessTokenSupplier, null);
    }

    @Override
    public String getClientID() {
        return clientId;
    }

    @Override
    public OkHttpClient.Builder setAuthOptions(OkHttpClient.Builder builder) {
        try {
            if (SKIP_HOSTNAME_VERIFICATION) {
                builder.hostnameVerifier((hostname, session) -> true);
            }

            if (trustManagers != null && trustManagers.length > 0) {
                SSLContext sslContext = SSLContext.getInstance("TLS");
                sslContext.init(null, trustManagers, null);
                builder.sslSocketFactory(sslContext.getSocketFactory(), (X509TrustManager) trustManagers[0]);
            }

            return builder
                    .addInterceptor(chain -> {
                        var token = accessTokenSupplier.get();
                        if (token == null || token.isBlank()) {
                            throw new IllegalStateException("OAuth access token is missing");
                        }

                        var newRequest = chain.request().newBuilder()
                                .header(AUTHORIZATION_HEADER, "Bearer " + token)
                                .build();
                        return chain.proceed(newRequest);
                    });
        } catch (Exception e) {
            throw new RuntimeException(e);
        }
    }

    @Override
    public void setAuthOptions(MqttConnectOptions mqttConnectOptions) {
        try {
            mqttConnectOptions.setHttpsHostnameVerificationEnabled(!SKIP_HOSTNAME_VERIFICATION);
            if (trustManagers != null && trustManagers.length > 0) {
                SSLContext sslContext = SSLContext.getInstance("TLS");
                sslContext.init(null, trustManagers, null);
                mqttConnectOptions.setSocketFactory(sslContext.getSocketFactory());
            }
        } catch (Exception e) {
            throw new RuntimeException(e);
        }
    }
}
