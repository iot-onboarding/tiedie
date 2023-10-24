// Copyright (c) 2023, Cisco and/or its affiliates.
// All rights reserved.
// See license in distribution for details.

package com.example.tiediesampleapp.config;

import java.io.FileInputStream;
import java.io.InputStream;
import java.security.KeyStore;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.stereotype.Component;

import com.cisco.tiedie.auth.ApiKeyAuthenticator;
import com.cisco.tiedie.auth.Authenticator;
import com.cisco.tiedie.auth.CertificateAuthenticator;
import com.cisco.tiedie.clients.OnboardingClient;

@Component
@Configuration
public class OnboardingAppConfig {
    @Value("${client.ca_path}")
    private String caPath;

    @Value("${onboarding-app.key:#{null}}")
    private String onboardingAppKey;

    @Value("${onboarding-app.id}")
    private String onboardingAppId;

    @Value("${onboarding-app.base_url}")
    private String onboardingAppBaseUrl;

    @Value("${onboarding-app.cert_path:#{null}}")
    private String onboardingAppCertPath;

    @Bean
    public OnboardingClient getOnboardingClient() throws Exception {
        Authenticator authenticator;
        try (InputStream caStream = new FileInputStream(caPath)) {
            if (onboardingAppCertPath != null && !onboardingAppCertPath.isEmpty()) {
                InputStream clientKeystoreStream = new FileInputStream(onboardingAppCertPath);
                KeyStore keyStore = KeyStore.getInstance("PKCS12");
                keyStore.load(clientKeystoreStream, "".toCharArray());
    
                authenticator = CertificateAuthenticator.create(caStream, keyStore, "");
            } else {
                authenticator = ApiKeyAuthenticator.create(caStream, onboardingAppId, onboardingAppKey);
            }

            return new OnboardingClient(onboardingAppBaseUrl, authenticator);
        }
    }
}
