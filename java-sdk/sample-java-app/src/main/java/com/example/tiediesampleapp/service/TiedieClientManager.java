// Copyright (c) 2023, Cisco Systems, Inc. and/or its affiliates.
// All rights reserved.
// See LICENSE file in this distribution.
// SPDX-License-Identifier: Apache-2.0

package com.example.tiediesampleapp.service;

import com.cisco.tiedie.auth.ApiKeyAuthenticator;
import com.cisco.tiedie.auth.Authenticator;
import com.cisco.tiedie.auth.CertificateAuthenticator;
import com.cisco.tiedie.auth.OAuth2Authenticator;
import com.cisco.tiedie.clients.ControlClient;
import com.cisco.tiedie.clients.DataReceiverClient;
import com.cisco.tiedie.clients.OnboardingClient;
import com.cisco.tiedie.dto.HttpResponse;
import com.cisco.tiedie.dto.scim.AppCertificateInfo;
import com.cisco.tiedie.dto.scim.EndpointApp;
import com.cisco.tiedie.dto.scim.EndpointAppListResponse;
import com.cisco.tiedie.dto.scim.EndpointAppType;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import javax.naming.InvalidNameException;
import javax.naming.ldap.LdapName;
import javax.naming.ldap.Rdn;
import javax.security.auth.x500.X500Principal;
import java.io.FileInputStream;
import java.io.InputStream;
import java.security.KeyStore;
import java.security.KeyStoreException;
import java.security.cert.CertificateEncodingException;
import java.security.cert.CertificateFactory;
import java.security.cert.X509Certificate;
import java.util.ArrayList;
import java.util.Base64;
import java.util.Enumeration;
import java.util.List;
import java.util.Optional;

@Service
public class TiedieClientManager {
    @Value("${client.ca_path}")
    private String clientCaPath;

    @Value("${onboarding-app.base_url}")
    private String onboardingAppBaseUrl;

    @Value("${onboarding-app.id}")
    private String onboardingAppId;

    @Value("${onboarding-app.key:#{null}}")
    private String onboardingAppKey;

    @Value("${onboarding-app.cert_path:#{null}}")
    private String onboardingAppCertPath;

    @Value("${control-app.base_url}")
    private String controlAppBaseUrl;

    @Value("${control-app.id}")
    private String controlAppId;

    @Value("${control-app.auth-type:token}")
    private String controlAppAuthType;

    @Value("${control-app.cert_path:#{null}}")
    private String controlAppCertPath;

    @Value("${data-app.base_url}")
    private String dataAppBaseUrl;

    @Value("${data-app.id}")
    private String dataAppId;

    @Value("${data-app.auth-type:token}")
    private String dataAppAuthType;

    @Value("${data-app.cert_path:#{null}}")
    private String dataAppCertPath;

    @Value("${data-app.mqtt-type:client}")
    private String dataAppMqttType;

    @Value("${data-app.username:#{null}}")
    private String dataAppUsername;

    @Value("${data-app.password:#{null}}")
    private String dataAppPassword;

    @Value("${data-app.broker-ca-path:#{null}}")
    private String dataAppBrokerCaPath;

    private final OAuthService oAuthService;

    private volatile boolean initialized;

    private OnboardingClient onboardingClient;
    private ControlClient controlClient;
    private DataReceiverClient dataReceiverClient;
    private EndpointApp controlEndpointApp;
    private EndpointApp dataEndpointApp;

    public TiedieClientManager(OAuthService oAuthService) {
        this.oAuthService = oAuthService;
    }

    public synchronized void invalidate() {
        if (dataReceiverClient != null) {
            try {
                dataReceiverClient.disconnect();
            } catch (Exception ignored) {
            }
        }

        initialized = false;
        onboardingClient = null;
        controlClient = null;
        dataReceiverClient = null;
        controlEndpointApp = null;
        dataEndpointApp = null;
    }

    public boolean isOauthEnabled() {
        return oAuthService.isEnabled();
    }

    public boolean hasOauthToken() {
        return oAuthService.hasValidToken();
    }

    public OnboardingClient getOnboardingClient() throws Exception {
        initializeIfNeeded();
        return onboardingClient;
    }

    public ControlClient getControlClient() throws Exception {
        initializeIfNeeded();
        return controlClient;
    }

    public DataReceiverClient getDataReceiverClient() throws Exception {
        initializeIfNeeded();
        return dataReceiverClient;
    }

    public EndpointApp getControlEndpointApp() throws Exception {
        initializeIfNeeded();
        return controlEndpointApp;
    }

    public EndpointApp getDataEndpointApp() throws Exception {
        initializeIfNeeded();
        return dataEndpointApp;
    }

    public List<EndpointApp> getDeviceEndpointApps() throws Exception {
        initializeIfNeeded();
        List<EndpointApp> apps = new ArrayList<>();
        if (controlEndpointApp != null) {
            apps.add(controlEndpointApp);
        }
        if (dataEndpointApp != null) {
            apps.add(dataEndpointApp);
        }
        return apps;
    }

    public String getDataAppMqttType() {
        return dataAppMqttType;
    }

    public String getDataAppBaseUrl() {
        return dataAppBaseUrl;
    }

    public String getDataAppUsername() {
        return dataAppUsername;
    }

    public String getDataAppPassword() {
        return dataAppPassword;
    }

    public String getDataAppBrokerCaPath() {
        return dataAppBrokerCaPath;
    }

    private synchronized void initializeIfNeeded() throws Exception {
        if (initialized) {
            return;
        }

        onboardingClient = new OnboardingClient(onboardingAppBaseUrl, createOnboardingAuthenticator());

        HttpResponse<EndpointAppListResponse> endpointAppsResponse = onboardingClient.getEndpointApps();
        List<EndpointApp> endpointApps = endpointAppsResponse.getBody() == null
                ? List.of()
                : Optional.ofNullable(endpointAppsResponse.getBody().getResources()).orElse(List.of());

        controlEndpointApp = findEndpointApp(endpointApps, EndpointAppType.DEVICE_CONTROL, controlAppId);
        if (controlEndpointApp == null && !oAuthService.isEnabled()) {
            controlEndpointApp = createControlEndpointApp(onboardingClient);
        }

        dataEndpointApp = findEndpointApp(endpointApps, EndpointAppType.TELEMETRY, dataAppId);
        if (dataEndpointApp == null) {
            dataEndpointApp = createDataEndpointApp(onboardingClient);
        }

        controlClient = new ControlClient(controlAppBaseUrl, createControlAuthenticator());
        dataReceiverClient = new DataReceiverClient(dataAppBaseUrl, createDataReceiverAuthenticator());
        initialized = true;
    }

    private EndpointApp findEndpointApp(List<EndpointApp> endpointApps, EndpointAppType type, String name) {
        return endpointApps.stream()
                .filter(app -> app.getApplicationType() == type)
                .filter(app -> name.equals(app.getApplicationName()))
                .findFirst()
                .orElse(null);
    }

    private EndpointApp createControlEndpointApp(OnboardingClient onboardingClient) throws Exception {
        EndpointApp.Builder builder = EndpointApp.builder()
                .applicationName(controlAppId)
                .applicationType(EndpointAppType.DEVICE_CONTROL);

        if ("cert".equalsIgnoreCase(controlAppAuthType) && hasValue(controlAppCertPath)) {
            try (InputStream caStream = new FileInputStream(clientCaPath);
                 InputStream keyStoreStream = new FileInputStream(controlAppCertPath)) {
                KeyStore keyStore = KeyStore.getInstance("PKCS12");
                keyStore.load(keyStoreStream, "".toCharArray());

                CertificateFactory certificateFactory = CertificateFactory.getInstance("X.509");
                X509Certificate caCert = (X509Certificate) certificateFactory.generateCertificate(caStream);

                builder.certificateInfo(AppCertificateInfo.builder()
                        .rootCA(getEncodedCert(caCert))
                        .subjectName(getCnFromKeyStore(keyStore))
                        .build());
            }
        }

        HttpResponse<EndpointApp> response = onboardingClient.createEndpointApp(builder.build());
        return response.getBody();
    }

    private EndpointApp createDataEndpointApp(OnboardingClient onboardingClient) throws Exception {
        EndpointApp endpointApp = EndpointApp.builder()
                .applicationName(dataAppId)
                .applicationType(EndpointAppType.TELEMETRY)
                .build();

        HttpResponse<EndpointApp> response = onboardingClient.createEndpointApp(endpointApp);
        return response.getBody();
    }

    private Authenticator createOnboardingAuthenticator() throws Exception {
        if (oAuthService.isEnabled()) {
            return createOAuthAuthenticator(onboardingAppId);
        }

        if (hasValue(onboardingAppCertPath)) {
            return createCertificateAuthenticator(onboardingAppCertPath);
        }

        return createApiKeyAuthenticator(onboardingAppId, onboardingAppKey, clientCaPath);
    }

    private Authenticator createControlAuthenticator() throws Exception {
        if (oAuthService.isEnabled()) {
            return createOAuthAuthenticator(controlAppId);
        }

        if (controlEndpointApp != null && controlEndpointApp.getCertificateInfo() != null) {
            return createCertificateAuthenticator(controlAppCertPath);
        }

        if (controlEndpointApp == null || !hasValue(controlEndpointApp.getClientToken())) {
            throw new IllegalStateException("Control endpoint app is not initialized");
        }

        return createApiKeyAuthenticator(controlAppId, controlEndpointApp.getClientToken(), clientCaPath);
    }

    private Authenticator createDataReceiverAuthenticator() throws Exception {
        if ("broker".equalsIgnoreCase(dataAppMqttType)) {
            if (!hasValue(dataAppUsername) || !hasValue(dataAppPassword)) {
                throw new IllegalStateException("Broker MQTT mode requires data-app.username and data-app.password");
            }

            String brokerCaPath = hasValue(dataAppBrokerCaPath) ? dataAppBrokerCaPath : clientCaPath;
            return createApiKeyAuthenticator(dataAppUsername, dataAppPassword, brokerCaPath);
        }

        if (dataEndpointApp != null && dataEndpointApp.getCertificateInfo() != null) {
            return createCertificateAuthenticator(dataAppCertPath);
        }

        if (dataEndpointApp == null || !hasValue(dataEndpointApp.getClientToken())) {
            throw new IllegalStateException("Data endpoint app is not initialized");
        }

        return createApiKeyAuthenticator(dataEndpointApp.getId(), dataEndpointApp.getClientToken(), clientCaPath);
    }

    private Authenticator createApiKeyAuthenticator(String appId, String key, String caPath) throws Exception {
        try (InputStream caStream = new FileInputStream(caPath)) {
            return ApiKeyAuthenticator.create(caStream, appId, key);
        }
    }

    private Authenticator createCertificateAuthenticator(String certPath) throws Exception {
        if (!hasValue(certPath)) {
            throw new IllegalStateException("Certificate path is missing");
        }

        try (InputStream caStream = new FileInputStream(clientCaPath);
             InputStream keyStoreStream = new FileInputStream(certPath)) {
            KeyStore keyStore = KeyStore.getInstance("PKCS12");
            keyStore.load(keyStoreStream, "".toCharArray());
            return CertificateAuthenticator.create(caStream, keyStore, "");
        }
    }

    private Authenticator createOAuthAuthenticator(String appId) throws Exception {
        if (hasValue(clientCaPath)) {
            try (InputStream caStream = new FileInputStream(clientCaPath)) {
                return OAuth2Authenticator.create(caStream, appId, oAuthService::getAccessToken);
            }
        }

        return OAuth2Authenticator.create(appId, oAuthService::getAccessToken);
    }

    private String getCnFromKeyStore(KeyStore keyStore) {
        try {
            Enumeration<String> aliases = keyStore.aliases();
            String alias = aliases.nextElement();
            X509Certificate certificate = (X509Certificate) keyStore.getCertificate(alias);
            X500Principal principal = certificate.getSubjectX500Principal();
            LdapName ldapName = new LdapName(principal.getName());

            Optional<Rdn> rdn = ldapName.getRdns().stream()
                    .filter(item -> item.getType().equalsIgnoreCase("CN"))
                    .findFirst();

            if (rdn.isEmpty()) {
                throw new IllegalStateException("No CN found in certificate");
            }

            return rdn.get().getValue().toString();
        } catch (KeyStoreException | InvalidNameException e) {
            throw new RuntimeException(e);
        }
    }

    private String getEncodedCert(X509Certificate certificate) throws CertificateEncodingException {
        byte[] encoded = certificate.getEncoded();
        byte[] b64Key = Base64.getEncoder().encode(encoded);
        return new String(b64Key);
    }

    private static boolean hasValue(String value) {
        return value != null && !value.isBlank();
    }
}
