// Copyright (c) 2023, Cisco Systems, Inc. and/or its affiliates.
// All rights reserved.
// See LICENSE file in this distribution.
// SPDX-License-Identifier: Apache-2.0

package com.cisco.tiedie.auth;

import com.cisco.tiedie.clients.OnboardingClient;
import com.cisco.tiedie.clients.utils.CertificateHelper;
import okhttp3.HttpUrl;
import okhttp3.mockwebserver.MockResponse;
import okhttp3.mockwebserver.MockWebServer;
import okhttp3.mockwebserver.RecordedRequest;
import org.junit.jupiter.api.Test;

import java.io.InputStream;
import java.security.cert.X509Certificate;
import java.util.concurrent.atomic.AtomicReference;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;

class OAuth2AuthenticatorTest {
    private static final X509Certificate ROOT_CERT;

    static {
        try {
            var rootCertSubject = CertificateHelper.createX500Name("ca");
            var rootKeyPair = CertificateHelper.createKeyPair();
            ROOT_CERT = CertificateHelper.createCaCertificate(rootKeyPair, rootCertSubject);
        } catch (Exception e) {
            throw new RuntimeException(e);
        }
    }

    @Test
    void tokenSupplierIsAppliedPerRequest() throws Exception {
        MockWebServer server = new MockWebServer();
        server.start();
        try {
            server.enqueue(new MockResponse().setResponseCode(200).setBody("{\"Resources\":[]}"));
            server.enqueue(new MockResponse().setResponseCode(200).setBody("{\"Resources\":[]}"));

            AtomicReference<String> tokenRef = new AtomicReference<>("token-1");
            InputStream caStream = CertificateHelper.createPemInputStream(ROOT_CERT);
            var authenticator = OAuth2Authenticator.create(caStream, "oauth-client", tokenRef::get);
            HttpUrl baseUrl = server.url("/scim/v2");

            OnboardingClient client = new OnboardingClient(baseUrl.toString(), authenticator);
            client.getDevices();

            RecordedRequest first = server.takeRequest();
            assertEquals("Bearer token-1", first.getHeader("Authorization"));

            tokenRef.set("token-2");
            client.getDevices();
            RecordedRequest second = server.takeRequest();
            assertEquals("Bearer token-2", second.getHeader("Authorization"));
        } finally {
            server.shutdown();
        }
    }

    @Test
    void missingTokenFailsFast() throws Exception {
        MockWebServer server = new MockWebServer();
        server.start();
        try {
            server.enqueue(new MockResponse().setResponseCode(200).setBody("{\"Resources\":[]}"));

            AtomicReference<String> tokenRef = new AtomicReference<>(null);
            InputStream caStream = CertificateHelper.createPemInputStream(ROOT_CERT);
            var authenticator = OAuth2Authenticator.create(caStream, "oauth-client", tokenRef::get);
            HttpUrl baseUrl = server.url("/scim/v2");
            OnboardingClient client = new OnboardingClient(baseUrl.toString(), authenticator);

            assertThrows(RuntimeException.class, client::getDevices);
        } finally {
            server.shutdown();
        }
    }
}
