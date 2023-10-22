// Copyright (c) 2023, Cisco and/or its affiliates.
// All rights reserved.
// See license in distribution for details.

package com.cisco.tiedie.clients;


import com.cisco.tiedie.auth.ApiKeyAuthenticator;
import com.cisco.tiedie.auth.CertificateAuthenticator;
import com.cisco.tiedie.dto.control.TiedieResponse;
import com.cisco.tiedie.dto.control.TiedieStatus;
import com.cisco.tiedie.dto.scim.Device;
import com.cisco.tiedie.dto.scim.ZigbeeExtension;
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
import java.util.List;
import java.util.UUID;
import java.util.stream.Stream;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Named.named;
import static org.junit.jupiter.params.provider.Arguments.arguments;

abstract class ControlClientTest {
    static final String CONTROL_APP_ID = "control-app";
    private static final String CONTROL_API_KEY = UUID.randomUUID().toString();
    private static final String CONTROL_CERT_PATH = "/control-app.p12";

    private static final String CA_PEM_PATH = "/ca.pem";

    static MockWebServer mockWebServer = new MockWebServer();

    static ControlClient controlClientWithCert;
    static ControlClient controlClientWithKey;

    @BeforeAll
    static void setup() throws Exception {
        ObjectMapperSingleton
                .getInstance()
                .enable(SerializationFeature.INDENT_OUTPUT);

        mockWebServer = new MockWebServer();
        mockWebServer.start();

        controlClientWithCert = ControlClientTest.createControlClientWithCert();
        controlClientWithKey = ControlClientTest.createControlAppWithKey();
    }

    @AfterAll
    static void teardown() throws IOException {
        mockWebServer.shutdown();
    }

    private static ControlClient createControlClientWithCert() {
        try (InputStream caStream = ControlClientTest.class.getResourceAsStream(CA_PEM_PATH);
             InputStream clientKeystoreStream = ControlClientTest.class.getResourceAsStream(CONTROL_CERT_PATH)) {
            KeyStore keyStore = KeyStore.getInstance("PKCS12");
            keyStore.load(clientKeystoreStream, "".toCharArray());

            CertificateAuthenticator authenticator = CertificateAuthenticator.create(caStream, keyStore, "");

            HttpUrl baseUrl = mockWebServer.url("/control");
            return new ControlClient(baseUrl.toString(), authenticator);
        } catch (Exception e) {
            return null;
        }
    }

    private static ControlClient createControlAppWithKey() {
        try (InputStream caStream = ControlClientTest.class.getResourceAsStream(CA_PEM_PATH)) {
            ApiKeyAuthenticator authenticator = ApiKeyAuthenticator.create(caStream, CONTROL_APP_ID, CONTROL_API_KEY);

            HttpUrl baseUrl = mockWebServer.url("/control");
            return new ControlClient(baseUrl.toString(), authenticator);
        } catch (Exception e) {
            return null;
        }
    }

    @MethodSource("clientProvider")
    @ParameterizedTest(name = "{0}")
    abstract void introduce(ControlClient controlClient) throws Exception;

    @MethodSource("clientProvider")
    @ParameterizedTest(name = "{0}")
    abstract void connect(ControlClient controlClient) throws Exception;

    @MethodSource("clientProvider")
    @ParameterizedTest(name = "{0}")
    abstract void disconnect(ControlClient controlClient) throws Exception;

    @MethodSource("clientProvider")
    @ParameterizedTest(name = "{0}")
    abstract void discover(ControlClient controlClient) throws Exception;

    @MethodSource("clientProvider")
    @ParameterizedTest(name = "{0}")
    abstract void read(ControlClient controlClient) throws Exception;

    @MethodSource("clientProvider")
    @ParameterizedTest(name = "{0}")
    abstract void write(ControlClient controlClient) throws Exception;

    @MethodSource("clientProvider")
    @ParameterizedTest(name = "{0}")
    abstract void subscribe(ControlClient controlClient) throws Exception;

    @MethodSource("clientProvider")
    @ParameterizedTest(name = "{0}")
    abstract void unsubscribe(ControlClient controlClient) throws Exception;

    @Test
    @DisplayName("Test API Key")
    void testApiKey() throws Exception {
        var controlClient = controlClientWithKey;

        mockWebServer.enqueue(
                new MockResponse()
                        .setResponseCode(200)
                        .setBody("{\n" +
                                "  \"status\" : \"SUCCESS\"\n" +
                                "}")
        );

        var deviceId = UUID.randomUUID().toString();

        var device = Device.builder()
                .id(deviceId)
                .deviceDisplayName("Zigbee Monitor")
                .adminState(false)
                .zigbeeExtension(ZigbeeExtension.builder()
                        .versionSupport(List.of("3.0"))
                        .deviceEui64Address("50325FFFFEE76728")
                        .build())
                .build();

        TiedieResponse<Void> response = controlClient.introduce(device);

        assertEquals(200, response.getHttpStatusCode());
        assertEquals("OK", response.getHttpMessage());
        assertEquals(TiedieStatus.SUCCESS, response.getStatus());

        RecordedRequest request = mockWebServer.takeRequest();
        assertEquals("/control/connectivity/introduce", request.getPath());
        assertEquals("POST", request.getMethod());
        assertEquals("{\n" +
                "  \"technology\" : \"zigbee\",\n" +
                "  \"id\" : \"" + deviceId + "\",\n" +
                "  \"controlApp\" : \"" + CONTROL_APP_ID + "\"\n" +
                "}", request.getBody().readUtf8());

        assertEquals(CONTROL_API_KEY, request.getHeader("x-api-key"));
    }

    static Stream<Arguments> clientProvider() {
        return Stream.of(
                arguments(named("With cert", controlClientWithCert)),
                arguments(named("With key", controlClientWithKey))
        );
    }
}

