// Copyright (c) 2023, Cisco Systems, Inc. and/or its affiliates.
// All rights reserved.
// See LICENSE file in this distribution.
// SPDX-License-Identifier: Apache-2.0

package com.cisco.tiedie.clients;

import com.cisco.tiedie.auth.ApiKeyAuthenticator;
import com.cisco.tiedie.auth.CertificateAuthenticator;
import com.cisco.tiedie.clients.utils.CertificateHelper;
import com.cisco.tiedie.dto.HttpResponse;
import com.cisco.tiedie.dto.scim.AppCertificateInfo;
import com.cisco.tiedie.dto.scim.BleExtension;
import com.cisco.tiedie.dto.scim.Device;
import com.cisco.tiedie.dto.scim.DeviceListResponse;
import com.cisco.tiedie.dto.scim.EndpointApp;
import com.cisco.tiedie.dto.scim.EndpointAppListResponse;
import com.cisco.tiedie.dto.scim.EndpointAppType;
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
import static org.junit.jupiter.api.Assertions.assertNotNull;
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

    @DisplayName("Get Devices")
    @ParameterizedTest(name = "{0}")
    @MethodSource("clientProvider")
    void getDevices(OnboardingClient onboardingClient) throws Exception {
        String firstDeviceId = UUID.randomUUID().toString();
        String secondDeviceId = UUID.randomUUID().toString();

        mockWebServer.enqueue(
                new MockResponse()
                        .setResponseCode(200)
                        .setBody("{\n" +
                                "  \"totalResults\" : 2,\n" +
                                "  \"startIndex\" : 1,\n" +
                                "  \"itemsPerPage\" : 2,\n" +
                                "  \"Resources\" : [\n" +
                                "    {\n" +
                                "      \"schemas\" : [ \"urn:ietf:params:scim:schemas:core:2.0:Device\" ],\n" +
                                "      \"id\" : \"" + firstDeviceId + "\",\n" +
                                "      \"displayName\" : \"Device One\",\n" +
                                "      \"active\" : true\n" +
                                "    },\n" +
                                "    {\n" +
                                "      \"schemas\" : [ \"urn:ietf:params:scim:schemas:core:2.0:Device\" ],\n" +
                                "      \"id\" : \"" + secondDeviceId + "\",\n" +
                                "      \"displayName\" : \"Device Two\",\n" +
                                "      \"active\" : false\n" +
                                "    }\n" +
                                "  ]\n" +
                                "}"));

        HttpResponse<DeviceListResponse> response = onboardingClient.getDevices();

        assertEquals(200, response.getStatusCode());
        assertNotNull(response.getBody());
        assertEquals(2, response.getBody().getTotalResults());
        assertEquals(1, response.getBody().getStartIndex());
        assertEquals(2, response.getBody().getItemsPerPage());
        assertNotNull(response.getBody().getResources());
        assertEquals(2, response.getBody().getResources().size());
        assertEquals(firstDeviceId, response.getBody().getResources().get(0).getId());
        assertEquals(secondDeviceId, response.getBody().getResources().get(1).getId());

        RecordedRequest request = mockWebServer.takeRequest();
        assertEquals("/scim/v2/Devices", request.getPath());
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

    @DisplayName("Create Endpoint App")
    @ParameterizedTest(name = "{0}")
    @MethodSource("clientProvider")
    void createEndpointApp(OnboardingClient onboardingClient) throws Exception {
        String endpointAppId = UUID.randomUUID().toString();

        mockWebServer.enqueue(
                new MockResponse()
                        .setResponseCode(201)
                        .setBody("{\n" +
                                "  \"schemas\" : [ \"urn:ietf:params:scim:schemas:core:2.0:EndpointApp\" ],\n" +
                                "  \"id\" : \"" + endpointAppId + "\",\n" +
                                "  \"applicationType\" : \"telemetry\",\n" +
                                "  \"applicationName\" : \"Telemetry App\",\n" +
                                "  \"certificateInfo\" : {\n" +
                                "    \"rootCA\" : \"-----BEGIN CERTIFICATE-----ROOT-----END CERTIFICATE-----\",\n" +
                                "    \"subjectName\" : \"CN=telemetry-app\"\n" +
                                "  },\n" +
                                "  \"clientToken\" : \"endpoint-token\"\n" +
                                "}"));

        EndpointApp endpointApp = EndpointApp.builder()
                .applicationType(EndpointAppType.TELEMETRY)
                .applicationName("Telemetry App")
                .certificateInfo(AppCertificateInfo.builder()
                        .rootCA("-----BEGIN CERTIFICATE-----ROOT-----END CERTIFICATE-----")
                        .subjectName("CN=telemetry-app")
                        .build())
                .build();

        HttpResponse<EndpointApp> response = onboardingClient.createEndpointApp(endpointApp);

        assertEquals(201, response.getStatusCode());
        assertNotNull(response.getBody());
        assertEquals(endpointAppId, response.getBody().getId());
        assertEquals(EndpointAppType.TELEMETRY, response.getBody().getApplicationType());
        assertEquals("Telemetry App", response.getBody().getApplicationName());

        RecordedRequest request = mockWebServer.takeRequest();
        assertEquals("/scim/v2/EndpointApps", request.getPath());
        assertEquals("POST", request.getMethod());
        assertEquals("application/scim+json; charset=utf-8", request.getHeader("Content-Type"));
        assertNotNull(request.getBody().readUtf8());
    }

    @DisplayName("Get Endpoint App")
    @ParameterizedTest(name = "{0}")
    @MethodSource("clientProvider")
    void getEndpointApp(OnboardingClient onboardingClient) throws Exception {
        String endpointAppId = UUID.randomUUID().toString();

        mockWebServer.enqueue(
                new MockResponse()
                        .setResponseCode(200)
                        .setBody("{\n" +
                                "  \"schemas\" : [ \"urn:ietf:params:scim:schemas:core:2.0:EndpointApp\" ],\n" +
                                "  \"id\" : \"" + endpointAppId + "\",\n" +
                                "  \"applicationType\" : \"telemetry\",\n" +
                                "  \"applicationName\" : \"Telemetry App\",\n" +
                                "  \"certificateInfo\" : {\n" +
                                "    \"rootCA\" : \"-----BEGIN CERTIFICATE-----ROOT-----END CERTIFICATE-----\",\n" +
                                "    \"subjectName\" : \"CN=telemetry-app\"\n" +
                                "  },\n" +
                                "  \"clientToken\" : \"endpoint-token\"\n" +
                                "}"));
        mockWebServer.enqueue(
                new MockResponse()
                        .setStatus("HTTP/1.1 404 Not Found")
                        .setBody("{\n" +
                                "  \"detail\" : \"EndpointApp not found\",\n" +
                                "  \"status\" : 404,\n" +
                                "}"));

        HttpResponse<EndpointApp> response = onboardingClient.getEndpointApp(endpointAppId);
        assertEquals(200, response.getStatusCode());
        assertNotNull(response.getBody());
        assertEquals(endpointAppId, response.getBody().getId());
        assertEquals(EndpointAppType.TELEMETRY, response.getBody().getApplicationType());

        response = onboardingClient.getEndpointApp("1234");
        assertEquals(404, response.getStatusCode());
        assertEquals("Not Found", response.getMessage());
        assertNull(response.getBody());

        RecordedRequest request = mockWebServer.takeRequest();
        assertEquals("/scim/v2/EndpointApps/" + endpointAppId, request.getPath());
        assertEquals("GET", request.getMethod());

        request = mockWebServer.takeRequest();
        assertEquals("/scim/v2/EndpointApps/1234", request.getPath());
        assertEquals("GET", request.getMethod());
    }

    @DisplayName("Get Endpoint Apps")
    @ParameterizedTest(name = "{0}")
    @MethodSource("clientProvider")
    void getEndpointApps(OnboardingClient onboardingClient) throws Exception {
        String telemetryId = UUID.randomUUID().toString();
        String controlId = UUID.randomUUID().toString();

        mockWebServer.enqueue(
                new MockResponse()
                        .setResponseCode(200)
                        .setBody("{\n" +
                                "  \"totalResults\" : 2,\n" +
                                "  \"startIndex\" : 1,\n" +
                                "  \"itemsPerPage\" : 2,\n" +
                                "  \"Resources\" : [\n" +
                                "    {\n" +
                                "      \"schemas\" : [ \"urn:ietf:params:scim:schemas:core:2.0:EndpointApp\" ],\n" +
                                "      \"id\" : \"" + telemetryId + "\",\n" +
                                "      \"applicationType\" : \"telemetry\",\n" +
                                "      \"applicationName\" : \"Telemetry App\",\n" +
                                "      \"clientToken\" : \"telemetry-token\"\n" +
                                "    },\n" +
                                "    {\n" +
                                "      \"schemas\" : [ \"urn:ietf:params:scim:schemas:core:2.0:EndpointApp\" ],\n" +
                                "      \"id\" : \"" + controlId + "\",\n" +
                                "      \"applicationType\" : \"deviceControl\",\n" +
                                "      \"applicationName\" : \"Control App\",\n" +
                                "      \"clientToken\" : \"control-token\"\n" +
                                "    }\n" +
                                "  ]\n" +
                                "}"));

        HttpResponse<EndpointAppListResponse> response = onboardingClient.getEndpointApps();

        assertEquals(200, response.getStatusCode());
        assertNotNull(response.getBody());
        assertEquals(2, response.getBody().getTotalResults());
        assertEquals(1, response.getBody().getStartIndex());
        assertEquals(2, response.getBody().getItemsPerPage());
        assertNotNull(response.getBody().getResources());
        assertEquals(2, response.getBody().getResources().size());
        assertEquals(telemetryId, response.getBody().getResources().get(0).getId());
        assertEquals(EndpointAppType.TELEMETRY, response.getBody().getResources().get(0).getApplicationType());
        assertEquals(controlId, response.getBody().getResources().get(1).getId());
        assertEquals(EndpointAppType.DEVICE_CONTROL, response.getBody().getResources().get(1).getApplicationType());

        RecordedRequest request = mockWebServer.takeRequest();
        assertEquals("/scim/v2/EndpointApps", request.getPath());
        assertEquals("GET", request.getMethod());
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
