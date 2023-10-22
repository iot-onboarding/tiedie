// Copyright (c) 2023, Cisco and/or its affiliates.
// All rights reserved.
// See license in distribution for details.

package com.example.tiediesampleapp.config;

import java.io.InputStream;
import java.security.KeyStore;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.stereotype.Component;

import com.cisco.tiedie.auth.CertificateAuthenticator;
import com.cisco.tiedie.clients.OnboardingClient;

@Component
@Configuration
public class OnboardingAppConfig {
    private static final String ONBOARDING_CERT_PATH = "/onboarding-app.p12";
    private static final String CA_PEM_PATH = "/ca.pem";
    private static final String ONBOARDING_BASE_URL = "https://localhost:8081/scim/v2";

    @Bean
    public OnboardingClient getOnboardingClient() throws Exception {
        try (InputStream caStream = OnboardingAppConfig.class.getResourceAsStream(CA_PEM_PATH);
                InputStream clientKeystoreStream = OnboardingAppConfig.class
                        .getResourceAsStream(ONBOARDING_CERT_PATH)) {
            KeyStore keyStore = KeyStore.getInstance("PKCS12");
            keyStore.load(clientKeystoreStream, "".toCharArray());

            CertificateAuthenticator authenticator = CertificateAuthenticator.create(caStream, keyStore, "");

            return new OnboardingClient(ONBOARDING_BASE_URL, authenticator);
        }
    }
}
