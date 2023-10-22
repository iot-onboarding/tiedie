// Copyright (c) 2023, Cisco and/or its affiliates.
// All rights reserved.
// See license in distribution for details.

package com.example.tiediesampleapp.config;

import java.io.InputStream;
import java.security.KeyStore;
import java.security.cert.CertificateFactory;
import java.security.cert.X509Certificate;
import java.util.List;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.stereotype.Component;

import com.cisco.tiedie.auth.ApiKeyAuthenticator;
import com.cisco.tiedie.auth.Authenticator;
import com.cisco.tiedie.auth.CertificateAuthenticator;
import com.cisco.tiedie.clients.DataReceiverClient;
import com.cisco.tiedie.clients.OnboardingClient;
import com.cisco.tiedie.dto.HttpResponse;
import com.cisco.tiedie.dto.scim.AppCertificateInfo;
import com.cisco.tiedie.dto.scim.EndpointApp;
import com.cisco.tiedie.dto.scim.EndpointAppType;

@Component
@Configuration
public class DataAppConfig extends ClientConfig {

    @Value("${data-app.id}")
    private String dataAppId;

    @Value("${data-app.auth-type}")
    private String dataAppAuthType;

    private static final String DATA_CERT_PATH = "/data-app.p12";
    private static final String DATA_BASE_URL = "ssl://localhost:8883";

    private EndpointApp createEndpointApp(OnboardingClient onboardingClient) throws Exception {
        var dataAppBuilder = EndpointApp.builder()
                .applicationName(dataAppId)
                .applicationType(EndpointAppType.TELEMETRY);

        if (dataAppAuthType.equals("cert")) {
            InputStream caStream = DataAppConfig.class.getResourceAsStream(CA_PEM_PATH);
            InputStream clientKeystoreStream = DataAppConfig.class.getResourceAsStream(DATA_CERT_PATH);
            KeyStore keyStore = KeyStore.getInstance("PKCS12");
            keyStore.load(clientKeystoreStream, "".toCharArray());

            CertificateFactory certificateFactory = CertificateFactory.getInstance("X.509");
            X509Certificate caCert = (X509Certificate) certificateFactory.generateCertificate(caStream);

            var rootCN = getCnFromCert(caCert);
            var cn = getCnFromKeyStore(keyStore);

            dataAppBuilder = dataAppBuilder
                    .certificateInfo(AppCertificateInfo.builder()
                            .rootCN(rootCN)
                            .subjectName(cn)
                            .build());
        }

        HttpResponse<EndpointApp> createEndpointAppResponse = onboardingClient
                .createEndpointApp(dataAppBuilder.build());

        return createEndpointAppResponse.getBody();
    }

    @Autowired
    @Bean
    @Qualifier("dataApp")
    public EndpointApp getDataAppEndpointApp(OnboardingClient onboardingClient) throws Exception {
        HttpResponse<List<EndpointApp>> httpResponse = onboardingClient.getEndpointApps();

        List<EndpointApp> endpointApps = httpResponse.getBody();

        if (endpointApps == null) {
            endpointApps = List.of();
        }

        return endpointApps.stream()
                .filter(app -> app.getApplicationType() == EndpointAppType.TELEMETRY
                        && app.getApplicationName().equals(dataAppId))
                .findFirst()
                .orElse(createEndpointApp(onboardingClient));
    }

    public Authenticator getAuthenticator(EndpointApp endpointApp) throws Exception {
        try (InputStream caStream = DataAppConfig.class.getResourceAsStream(CA_PEM_PATH);
                InputStream clientKeystoreStream = DataAppConfig.class.getResourceAsStream(DATA_CERT_PATH)) {
            if (endpointApp.getCertificateInfo() != null) {
                KeyStore keyStore = KeyStore.getInstance("PKCS12");
                keyStore.load(clientKeystoreStream, "".toCharArray());

                return CertificateAuthenticator.create(caStream, keyStore, "");
            }

            return ApiKeyAuthenticator.create(caStream, dataAppId,
                    endpointApp.getClientToken());
        }
    }

    @Autowired
    @Bean
    public DataReceiverClient getDataReceiverClient(OnboardingClient onboardingClient, @Qualifier("dataApp") EndpointApp endpointApp) throws Exception {
        Authenticator authenticator = getAuthenticator(endpointApp);

        return new DataReceiverClient(DATA_BASE_URL, authenticator);
    }

}
