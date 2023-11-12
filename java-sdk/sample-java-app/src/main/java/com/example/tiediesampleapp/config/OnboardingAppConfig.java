// Copyright (c) 2023, Cisco Systems, Inc. and/or its affiliates.
// All rights reserved.
// See LICENSE file in this distribution.
// SPDX-License-Identifier: Apache-2.0

package com.example.tiediesampleapp.config;

import java.io.FileInputStream;
import java.io.InputStream;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.stereotype.Component;

import com.cisco.tiedie.auth.ApiKeyAuthenticator;
import com.cisco.tiedie.clients.OnboardingClient;

@Component
@Configuration
public class OnboardingAppConfig {
    @Value("${client.ca_path}")
    private String caPath;

    @Value("${onboarding-app.key}")
    private String onboardingAppKey;

    @Value("${onboarding-app.id}")
    private String onboardingAppId;

    @Value("${onboarding-app.base_url}")
    private String onboardingAppBaseUrl;

    @Bean
    OnboardingClient getOnboardingClient() throws Exception {
        try (InputStream caStream = new FileInputStream(caPath)) {

            ApiKeyAuthenticator authenticator = ApiKeyAuthenticator.create(caStream, onboardingAppId, onboardingAppKey);

            return new OnboardingClient(onboardingAppBaseUrl, authenticator);
        }
    }
}
