// Copyright (c) 2023, Cisco and/or its affiliates.
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

/**
 * Client authentication method using API keys.
 * <p>
 * To create a {@link ApiKeyAuthenticator}, use the {@link ApiKeyAuthenticator#create(InputStream, String, String)} method:
 * <pre>
 * {@code
 * var authenticator = ApiKeyAuthenticator.create(inputStream, "app_id", "api_key");
 * }
 * </pre>
 */
@AllArgsConstructor(access = AccessLevel.PRIVATE)
public class ApiKeyAuthenticator implements Authenticator {

    private static final String API_KEY_HEADER = "x-api-key";
    private final String appId;
    private final String apiKey;

    private TrustManager[] trustManagers;

    /**
     * Create a new {@link ApiKeyAuthenticator} object.
     *
     * @param caInputStream {@link InputStream} that has the contents of the CA file in PEM format.
     * @param appId         App ID that created on the TieDie controller for authentication.
     * @param apiKey        API Key that was created on the TieDie controller for authentication.
     * @return Authenticator object that can be passed to a client.
     */
    public static ApiKeyAuthenticator create(InputStream caInputStream, String appId, String apiKey) {
        var trustManagers = Authenticator.getCaTrustManagers(caInputStream);

        return new ApiKeyAuthenticator(appId, apiKey, trustManagers);
    }

    @Override
    public String getClientID() {
        return appId;
    }

    @Override
    public OkHttpClient.Builder setAuthOptions(OkHttpClient.Builder builder) {
        try {
            SSLContext sslContext = SSLContext.getInstance("TLS");

            sslContext.init(null, trustManagers, null);

            if (SKIP_HOSTNAME_VERIFICATION) {
                builder.hostnameVerifier((hostname, session) -> true);
            }

            return builder
                    .sslSocketFactory(sslContext.getSocketFactory(), (X509TrustManager) trustManagers[0])
                    .addInterceptor(chain -> {
                        var original = chain.request();
                        var newRequest = original.newBuilder()
                                .header(API_KEY_HEADER, apiKey)
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
            SSLContext sslContext = SSLContext.getInstance("TLS");

            sslContext.init(null, trustManagers, null);

            mqttConnectOptions.setUserName(appId);
            mqttConnectOptions.setPassword(apiKey.toCharArray());
            mqttConnectOptions.setHttpsHostnameVerificationEnabled(!SKIP_HOSTNAME_VERIFICATION);
            // mqttConnectOptions.setSocketFactory(sslContext.getSocketFactory());
        } catch (Exception e) {
            throw new RuntimeException(e);
        }
    }
}
