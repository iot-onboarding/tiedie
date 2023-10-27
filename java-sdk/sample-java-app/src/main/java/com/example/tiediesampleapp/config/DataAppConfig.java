// Copyright (c) 2023, Cisco and/or its affiliates.
// All rights reserved.
// See LICENSE file in this distribution.
// SPDX-License-Identifier: Apache-2.0

package com.example.tiediesampleapp.config;

import java.io.FileInputStream;
import java.io.InputStream;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.stereotype.Component;

import com.cisco.tiedie.auth.ApiKeyAuthenticator;
import com.cisco.tiedie.auth.Authenticator;
import com.cisco.tiedie.clients.DataReceiverClient;
import com.cisco.tiedie.clients.OnboardingClient;

@Component
@Configuration
public class DataAppConfig extends ClientConfig {

    @Value("${data-app.id}")
    private String dataAppId;

    @Value("${data-app.auth-type:token}")
    private String dataAppAuthType;

    @Value("${data-app.key}")
    private String dataAppKey;

    @Value("${data-app.base_url}")
    private String dataAppBaseUrl;

    @Value("${client.ca_path}")
    private String caPath;

    @Autowired
    @Bean
    DataReceiverClient getDataReceiverClient(OnboardingClient onboardingClient) throws Exception {
        try (InputStream caStream = new FileInputStream(caPath)) {
            Authenticator authenticator = ApiKeyAuthenticator.create(caStream, dataAppId,
                    dataAppKey);
            return new DataReceiverClient(dataAppBaseUrl, authenticator);
        }
    }
}
