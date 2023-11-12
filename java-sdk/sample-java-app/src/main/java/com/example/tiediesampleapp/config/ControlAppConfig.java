// Copyright (c) 2023, Cisco Systems, Inc. and/or its affiliates.
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
import com.cisco.tiedie.clients.ControlClient;
import com.cisco.tiedie.clients.OnboardingClient;

@Component
@Configuration
public class ControlAppConfig extends ClientConfig {

    @Value("${control-app.id}")
    private String controlAppId;

    @Value("${control-app.auth-type:token}")
    private String controlAppAuthType;

    @Value("${control-app.key}")
    private String controlAppKey;

    @Value("${control-app.base_url}")
    private String controlAppBaseUrl;

    @Autowired
    @Bean
    ControlClient getControlClient(OnboardingClient onboardingClient) throws Exception {
        try (InputStream caStream = new FileInputStream(caPath)) {
            Authenticator authenticator = ApiKeyAuthenticator.create(caStream, controlAppId, controlAppKey);
            return new ControlClient(controlAppBaseUrl, authenticator);
        }
    }
}
