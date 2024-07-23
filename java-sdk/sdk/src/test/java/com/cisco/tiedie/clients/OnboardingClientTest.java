// Copyright (c) 2023, Cisco Systems, Inc. and/or its affiliates.
// All rights reserved.
// See LICENSE file in this distribution.
// SPDX-License-Identifier: Apache-2.0

package com.cisco.tiedie.clients;

import com.cisco.tiedie.auth.ApiKeyAuthenticator;
import com.cisco.tiedie.auth.CertificateAuthenticator;
import com.cisco.tiedie.clients.utils.CertificateHelper;
import com.cisco.tiedie.dto.HttpResponse;
import com.cisco.tiedie.dto.scim.BleExtension;
import com.cisco.tiedie.dto.scim.Device;
import com.cisco.tiedie.utils.ObjectMapperSingleton;
import com.fasterxml.jackson.databind.SerializationFeature;
import okhttp3.HttpUrl;
import okhttp3.mockwebserver.MockResponse;
import okhttp3.mockwebserver.MockWebServer;
import okhttp3.mockwebserver.RecordedRequest;
import org.junit.jupiter.api.AfterAll;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.Arguments;
import org.junit.jupiter.params.provider.MethodSource;

import java.io.IOException;
import java.io.InputStream;
import java.security.KeyStore;
import java.security.cert.X509Certificate;
import java.util.Arrays;
import java.util.UUID;
import java.util.stream.Stream;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Named.named;
import static org.junit.jupiter.params.provider.Arguments.arguments;

class OnboardingClientTest {
    private static final String ONBOARDING_APP_ID = "onboarding-app";
    private static final String ONBOARDING_API_KEY = UUID.randomUUID().toString();

    private static final MockWebServer mockWebServer = new MockWebServer();

    static X509Certificate rootCert;
    static KeyStore keyStore;

    static {
        try {
            var rootCertSubject = CertificateHelper.createX500Name("ca");
            var rootKeyPair = CertificateHelper.createKeyPair();

            rootCert = CertificateHelper.createCaCertificate(rootKeyPair, rootCertSubject);

            var appKeyPair = CertificateHelper.createKeyPair();
            var appCert = CertificateHelper.createAppCertificate(appKeyPair, ONBOARDING_APP_ID, rootKeyPair,
                    rootCertSubject);

            keyStore = CertificateHelper.createKeyStore(appKeyPair, appCert, ONBOARDING_APP_ID);
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    @BeforeAll
    static void setup() throws IOException {
        ObjectMapperSingleton
                .getInstance()
                .enable(SerializationFeature.INDENT_OUTPUT);

        mockWebServer.start();
    }

    @AfterAll
    static void teardown() throws IOException {
        mockWebServer.shutdown();
    }

    private static OnboardingClient createOnboardingClientWithCert() throws Exception {
        InputStream caStream = CertificateHelper.createPemInputStream(rootCert);
        CertificateAuthenticator authenticator = CertificateAuthenticator.create(caStream, keyStore, "");

        HttpUrl baseUrl = mockWebServer.url("/scim/v2");
        return new OnboardingClient(baseUrl.toString(), authenticator);
    }

    private static OnboardingClient createOnboardingClientWithKey() throws Exception {
        InputStream caStream = CertificateHelper.createPemInputStream(rootCert);
        ApiKeyAuthenticator authenticator = ApiKeyAuthenticator.create(caStream,
                ONBOARDING_APP_ID,
                ONBOARDING_API_KEY);

        HttpUrl baseUrl = mockWebServer.url("/scim/v2");
        return new OnboardingClient(baseUrl.toString(), authenticator);
    }

    public static Stream<Arguments> clientProvider() throws Exception {
        var onboardingClientWithCert = createOnboardingClientWithCert();

        var onboardingClientWithKey = createOnboardingClientWithKey();

        return Stream.of(
                arguments(named("With cert", onboardingClientWithCert)),
                arguments(named("With key", onboardingClientWithKey)));
    }

    @DisplayName("Create Device")
    @ParameterizedTest(name = "{0}")
    @MethodSource("clientProvider")
    void createDevice(OnboardingClient onboardingClient) throws Exception {
        String deviceId = UUID.randomUUID().toString();

        mockWebServer.enqueue(
                new MockResponse()
                        .setResponseCode(201)
                        .setBody("{\n" +
                                "  \"schemas\" : [ \"urn:ietf:params:scim:schemas:core:2.0:Device\", \"urn:ietf:params:scim:schemas:extension:ble:2.0:Device\" ],\n"
                                +
                                "\"id\" : \"" + deviceId + "\",\n" +
                                "  \"displayName\" : \"BLE Monitor\",\n" +
                                "  \"active\" : false,\n" +
                                "  \"urn:ietf:params:scim:schemas:extension:ble:2.0:Device\" : {\n" +
                                "    \"pairingMethods\" : [ \"urn:ietf:params:scim:schemas:extension:pairingPassKey:2.0:Device\" ],\n"
                                +
                                "    \"versionSupport\" : [ \"4.1\", \"4.2\", \"5.0\", \"5.1\", \"5.2\", \"5.3\" ],\n" +
                                "    \"deviceMacAddress\" : \"AA:BB:CC:11:22:33\",\n" +
                                "    \"isRandom\" : false,\n" +
                                "    \"urn:ietf:params:scim:schemas:extension:pairingPassKey:2.0:Device\" : {\n" +
                                "      \"key\" : 123456\n" +
                                "    }\n" +
                                "  }\n" +
                                "}"));

        var device = Device.builder()
                .displayName("BLE Monitor")
                .active(false)
                .bleExtension(BleExtension.builder()
                        .deviceMacAddress("AA:BB:CC:11:22:33")
                        .isRandom(false)
                        .versionSupport(Arrays.asList("4.1", "4.2", "5.0", "5.1", "5.2", "5.3"))
                        .pairingPassKey(new BleExtension.PairingPassKey(123456))
                        .build())
                .build();

        HttpResponse<Device> response = onboardingClient.createDevice(device);

        assertEquals(201, response.getStatusCode());
        device = response.getBody();

        assertEquals(deviceId, device.getId());

        RecordedRequest request = mockWebServer.takeRequest();
        assertEquals("/scim/v2/Devices", request.getPath());
        assertEquals("POST", request.getMethod());
    }

    @DisplayName("Get Device")
    @ParameterizedTest(name = "{0}")
    @MethodSource("clientProvider")
    void getDevice(OnboardingClient onboardingClient) throws Exception {
        String deviceId = UUID.randomUUID().toString();

        mockWebServer.enqueue(
                new MockResponse()
                        .setResponseCode(200)
                        .setBody("{\n" +
                                "  \"schemas\" : [ \"urn:ietf:params:scim:schemas:core:2.0:Device\", \"urn:ietf:params:scim:schemas:extension:ble:2.0:Device\" ],\n"
                                +
                                "\"id\" : \"" + deviceId + "\",\n" +
                                "  \"displayName\" : \"BLE Monitor\",\n" +
                                "  \"active\" : false,\n" +
                                "  \"urn:ietf:params:scim:schemas:extension:ble:2.0:Device\" : {\n" +
                                "    \"pairingMethods\" : [ \"urn:ietf:params:scim:schemas:extension:pairingPassKey:2.0:Device\" ],\n"
                                +
                                "    \"versionSupport\" : [ \"4.1\", \"4.2\", \"5.0\", \"5.1\", \"5.2\", \"5.3\" ],\n" +
                                "    \"deviceMacAddress\" : \"AA:BB:CC:11:22:33\",\n" +
                                "    \"isRandom\" : false,\n" +
                                "    \"urn:ietf:params:scim:schemas:extension:pairingPassKey:2.0:Device\" : {\n" +
                                "      \"key\" : 123456\n" +
                                "    }\n" +
                                "  }\n" +
                                "}"));
        mockWebServer.enqueue(new MockResponse()
                .setStatus("HTTP/1.1 404 Not Found")
                .setBody("{\n" +
                        "  \"schemas\" : [ \"urn:ietf:params:scim:schemas:core:2.0:Device\" ],\n" +
                        "  \"detail\" : \"User not found\",\n" +
                        "  \"status\" : 404,\n" +
                        "}"));

        HttpResponse<Device> response = onboardingClient.getDevice(deviceId);

        assertEquals(200, response.getStatusCode());
        var device = response.getBody();

        assertEquals(deviceId, device.getId());

        response = onboardingClient.getDevice("1234");

        assertEquals(404, response.getStatusCode());
        assertEquals("Not Found", response.getMessage());
        assertNull(response.getBody());

        RecordedRequest request = mockWebServer.takeRequest();
        assertEquals("/scim/v2/Devices/" + deviceId, request.getPath());
        assertEquals("GET", request.getMethod());

        request = mockWebServer.takeRequest();
        assertEquals("/scim/v2/Devices/1234", request.getPath());
        assertEquals("GET", request.getMethod());
    }

    @DisplayName("Delete Device")
    @ParameterizedTest(name = "{0}")
    @MethodSource("clientProvider")
    void deleteDevice(OnboardingClient onboardingClient) throws Exception {
        String deviceId = UUID.randomUUID().toString();

        mockWebServer.enqueue(new MockResponse().setStatus("HTTP/1.1 204 No Content"));

        HttpResponse<Void> response = onboardingClient.deleteDevice(deviceId);

        assertEquals(204, response.getStatusCode());
        assertEquals("No Content", response.getMessage());

        RecordedRequest request = mockWebServer.takeRequest();
        assertEquals("/scim/v2/Devices/" + deviceId, request.getPath());
        assertEquals("DELETE", request.getMethod());
        assertEquals(0, request.getBodySize());
    }

    @Test
    @DisplayName("Test API Key")
    void testApiKey() throws Exception {
        var onboardingClient = createOnboardingClientWithKey();

        mockWebServer.enqueue(new MockResponse());

        var deviceId = UUID.randomUUID().toString();

        onboardingClient.getDevice(deviceId);

        RecordedRequest request = mockWebServer.takeRequest();
        assertEquals(ONBOARDING_API_KEY, request.getHeader("x-api-key"));
    }
}