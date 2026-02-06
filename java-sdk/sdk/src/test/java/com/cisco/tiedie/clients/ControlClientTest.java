// Copyright (c) 2023, Cisco Systems, Inc. and/or its affiliates.
// All rights reserved.
// See LICENSE file in this distribution.
// SPDX-License-Identifier: Apache-2.0

package com.cisco.tiedie.clients;

import com.cisco.tiedie.auth.ApiKeyAuthenticator;
import com.cisco.tiedie.clients.utils.CertificateHelper;
import com.cisco.tiedie.dto.control.DataParameter;
import com.cisco.tiedie.dto.control.DataResponse;
import com.cisco.tiedie.dto.control.ble.BleDataParameter;
import com.cisco.tiedie.dto.nipc.*;
import com.cisco.tiedie.dto.scim.BleExtension;
import com.cisco.tiedie.dto.scim.Device;
import com.cisco.tiedie.utils.ObjectMapperSingleton;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import okhttp3.HttpUrl;
import okhttp3.mockwebserver.MockResponse;
import okhttp3.mockwebserver.MockWebServer;
import okhttp3.mockwebserver.RecordedRequest;
import org.junit.jupiter.api.Test;

import java.io.InputStream;
import java.security.cert.X509Certificate;
import java.util.Arrays;
import java.util.List;
import java.util.Map;
import java.util.UUID;

import static org.junit.jupiter.api.Assertions.*;

class ControlClientTest {
    private static final String CONTROL_APP_ID = "control-app";
    private static final String CONTROL_API_KEY = UUID.randomUUID().toString();

    private static final ObjectMapper MAPPER = ObjectMapperSingleton.getInstance();

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

    private static void assertJsonEquals(String expectedJson, String actualJson) throws Exception {
        JsonNode expected = MAPPER.readTree(expectedJson);
        JsonNode actual = MAPPER.readTree(actualJson);
        assertEquals(expected, actual);
    }

    private ControlClient createControlClient(MockWebServer mockWebServer) throws Exception {
        InputStream caStream = CertificateHelper.createPemInputStream(ROOT_CERT);
        ApiKeyAuthenticator authenticator = ApiKeyAuthenticator.create(caStream, CONTROL_APP_ID, CONTROL_API_KEY);
        HttpUrl baseUrl = mockWebServer.url("/nipc");

        return new ControlClient(baseUrl.toString(), authenticator);
    }

    private Device createBleDevice(String deviceId) {
        return Device.builder()
                .id(deviceId)
                .displayName("BLE Monitor")
                .active(false)
                .bleExtension(BleExtension.builder()
                        .deviceMacAddress("AA:BB:CC:11:22:33")
                        .isRandom(false)
                        .versionSupport(Arrays.asList("4.1", "4.2", "5.0", "5.1", "5.2", "5.3"))
                        .pairingPassKey(new BleExtension.PairingPassKey(123456))
                        .build())
                .build();
    }

    private SdfModel createComplexSdfModel() {
        // Based on the Python SDK SDF registration test, with additional nested event/action content.
        SdfModel model = new SdfModel();
        model.setNamespace(Map.of(
                "thermometer", "https://example.com/thermometer",
                "common", "https://example.com/common"
        ));
        model.setDefaultNamespace("thermometer");

        SdfProperty temperatureProperty = new SdfProperty();
        temperatureProperty.setObservable(true);
        temperatureProperty.setReadable(true);
        temperatureProperty.setWritable(true);
        temperatureProperty.setType("number");
        temperatureProperty.setUnit("Cel");
        temperatureProperty.setSdfProtocolMap(Map.of(
                "ble", Map.of(
                        "serviceID", "1809",
                        "characteristicID", "2A1C"
                )
        ));

        SdfProperty batteryLevelProperty = new SdfProperty();
        batteryLevelProperty.setReadable(true);
        batteryLevelProperty.setType("number");
        batteryLevelProperty.setUnit("%");
        batteryLevelProperty.setSdfProtocolMap(Map.of(
                "ble", Map.of(
                        "serviceID", "180F",
                        "characteristicID", "2A19"
                )
        ));

        SdfOutputData isPresentOutputData = new SdfOutputData();
        isPresentOutputData.setType("boolean");
        isPresentOutputData.setSdfProtocolMap(Map.of(
                "ble", Map.of(
                        "serviceID", "181A",
                        "characteristicID", "2A6E"
                )
        ));

        SdfEvent isPresentEvent = new SdfEvent();
        isPresentEvent.setDescription("Presence state changed");
        isPresentEvent.setSdfOutputData(isPresentOutputData);

        SdfAction toggleLedAction = new SdfAction();
        toggleLedAction.setDescription("Toggle LED state");
        toggleLedAction.setSdfProtocolMap(Map.of(
                "ble", Map.of(
                        "serviceID", "FF10",
                        "characteristicID", "FF11"
                )
        ));

        SdfObject healthSensor = new SdfObject();
        healthSensor.setDescription("Health sensor with BLE properties, events and actions");
        healthSensor.setSdfProperty(Map.of(
                "temperature", temperatureProperty,
                "batteryLevel", batteryLevelProperty
        ));
        healthSensor.setSdfEvent(Map.of(
                "isPresent", isPresentEvent
        ));
        healthSensor.setSdfAction(Map.of(
                "toggleLed", toggleLedAction
        ));

        model.setSdfObject(Map.of(
                "healthsensor", healthSensor
        ));

        SdfObject healthSensorRef = new SdfObject();
        healthSensorRef.setDescription("Health sensor endpoint");

        SdfThing thermometerThing = new SdfThing();
        thermometerThing.setDescription("Top-level thing containing the health sensor object");
        thermometerThing.setSdfObject(Map.of(
                "healthsensor", healthSensorRef
        ));

        model.setSdfThing(Map.of(
                "thermometerThing", thermometerThing
        ));

        return model;
    }

    @Test
    void connect() throws Exception {
        MockWebServer mockWebServer = new MockWebServer();
        mockWebServer.start();
        try {
            mockWebServer.enqueue(new MockResponse().setResponseCode(200)
                    .setBody("{" +
                            "\"sdfProtocolMap\":{\"ble\":[{" +
                            "\"serviceID\":\"1800\"," +
                            "\"characteristics\":[{" +
                            "\"characteristicID\":\"2a00\",\"flags\":[\"read\",\"write\"]" +
                            "}]" +
                            "}]}}"));

            ControlClient controlClient = createControlClient(mockWebServer);
            String deviceId = UUID.randomUUID().toString();

            NipcResponse<List<DataParameter>> response = controlClient.connect(createBleDevice(deviceId));
            assertTrue(response.isSuccess(), String.valueOf(response.getError()));
            assertNotNull(response.getBody());
            assertEquals(1, response.getBody().size());
            assertInstanceOf(BleDataParameter.class, response.getBody().get(0));

            RecordedRequest request = mockWebServer.takeRequest();
            assertEquals("POST", request.getMethod());
            assertEquals("/nipc/devices/" + deviceId + "/connections", request.getPath());
            assertJsonEquals("{" +
                    "\"sdfProtocolMap\":{\"ble\":{}}," +
                    "\"retries\":3," +
                    "\"retryMultipleAPs\":true" +
                    "}", request.getBody().readUtf8());
        } finally {
            mockWebServer.shutdown();
        }
    }

    @Test
    void getConnection() throws Exception {
        MockWebServer mockWebServer = new MockWebServer();
        mockWebServer.start();
        try {
            mockWebServer.enqueue(new MockResponse().setResponseCode(200)
                    .setBody("{" +
                            "\"sdfProtocolMap\":{\"ble\":[{" +
                            "\"serviceID\":\"1800\"," +
                            "\"characteristics\":[{" +
                            "\"characteristicID\":\"2a00\",\"flags\":[\"read\"]" +
                            "}]" +
                            "}]}}"));

            ControlClient controlClient = createControlClient(mockWebServer);
            String deviceId = UUID.randomUUID().toString();

            NipcResponse<List<DataParameter>> response = controlClient.getConnection(createBleDevice(deviceId));
            assertTrue(response.isSuccess(), String.valueOf(response.getError()));
            assertNotNull(response.getBody());
            assertEquals(1, response.getBody().size());

            RecordedRequest request = mockWebServer.takeRequest();
            assertEquals("GET", request.getMethod());
            assertEquals("/nipc/devices/" + deviceId + "/connections", request.getPath());
        } finally {
            mockWebServer.shutdown();
        }
    }

    @Test
    void discover() throws Exception {
        MockWebServer mockWebServer = new MockWebServer();
        mockWebServer.start();
        try {
            mockWebServer.enqueue(new MockResponse().setResponseCode(200)
                    .setBody("{" +
                            "\"sdfProtocolMap\":{\"ble\":[{" +
                            "\"serviceID\":\"1800\"," +
                            "\"characteristics\":[{" +
                            "\"characteristicID\":\"2a00\",\"flags\":[\"read\"]" +
                            "}]" +
                            "}]}}"));

            ControlClient controlClient = createControlClient(mockWebServer);
            String deviceId = UUID.randomUUID().toString();

            NipcResponse<List<DataParameter>> response = controlClient.discover(createBleDevice(deviceId));
            assertTrue(response.isSuccess(), String.valueOf(response.getError()));
            assertNotNull(response.getBody());
            assertEquals(1, response.getBody().size());

            RecordedRequest request = mockWebServer.takeRequest();
            assertEquals("PUT", request.getMethod());
            assertEquals("/nipc/devices/" + deviceId + "/connections", request.getPath());
        } finally {
            mockWebServer.shutdown();
        }
    }

    @Test
    void disconnect() throws Exception {
        MockWebServer mockWebServer = new MockWebServer();
        mockWebServer.start();
        try {
            mockWebServer.enqueue(new MockResponse().setResponseCode(200).setBody("{\"id\":\"abc\"}"));

            ControlClient controlClient = createControlClient(mockWebServer);
            String deviceId = UUID.randomUUID().toString();

            NipcResponse<TiedieDeviceResponse> response = controlClient.disconnect(createBleDevice(deviceId));
            assertTrue(response.isSuccess(), String.valueOf(response.getError()));
            assertNotNull(response.getBody());
            assertEquals("abc", response.getBody().getDeviceId());

            RecordedRequest request = mockWebServer.takeRequest();
            assertEquals("DELETE", request.getMethod());
            assertEquals("/nipc/devices/" + deviceId + "/connections", request.getPath());
        } finally {
            mockWebServer.shutdown();
        }
    }

    @Test
    void readAndWrite() throws Exception {
        MockWebServer mockWebServer = new MockWebServer();
        mockWebServer.start();
        try {
            mockWebServer.enqueue(new MockResponse().setResponseCode(200).setBody("{\"value\":\"00001111\"}"));
            mockWebServer.enqueue(new MockResponse().setResponseCode(200).setBody("{\"value\":\"00002222\"}"));

            ControlClient controlClient = createControlClient(mockWebServer);
            String deviceId = UUID.randomUUID().toString();
            Device device = createBleDevice(deviceId);

            NipcResponse<DataResponse> read = controlClient.read(device, "1800", "2a00");
            assertTrue(read.isSuccess(), String.valueOf(read.getError()));
            assertNotNull(read.getBody());
            assertEquals("00001111", read.getBody().getValue());

            RecordedRequest readRequest = mockWebServer.takeRequest();
            assertEquals("POST", readRequest.getMethod());
            assertEquals("/nipc/extensions/" + deviceId + "/properties/read", readRequest.getPath());

            NipcResponse<DataResponse> write = controlClient.write(device, "1800", "2a00", "00002222");
            assertTrue(write.isSuccess(), String.valueOf(write.getError()));
            assertNotNull(write.getBody());
            assertEquals("00002222", write.getBody().getValue());

            RecordedRequest writeRequest = mockWebServer.takeRequest();
            assertEquals("POST", writeRequest.getMethod());
            assertEquals("/nipc/extensions/" + deviceId + "/properties/write", writeRequest.getPath());
        } finally {
            mockWebServer.shutdown();
        }
    }

    @Test
    void propertyApis() throws Exception {
        MockWebServer mockWebServer = new MockWebServer();
        mockWebServer.start();
        try {
            String deviceId = UUID.randomUUID().toString();
            String propertyRef = "https://example.com/thermometer#/sdfObject/healthsensor/sdfProperty/temperature";

            mockWebServer.enqueue(new MockResponse().setResponseCode(200)
                    .setBody("[{\"property\":\"" + propertyRef + "\",\"value\":\"dGVzdA==\"}]"));
            mockWebServer.enqueue(new MockResponse().setResponseCode(200)
                    .setBody("[{\"status\":200}]"));

            ControlClient controlClient = createControlClient(mockWebServer);

            NipcResponse<List<PropertyReadResult>> readResponse = controlClient.readProperty(deviceId, propertyRef);
            assertTrue(readResponse.isSuccess(), String.valueOf(readResponse.getError()));
            assertNotNull(readResponse.getBody());
            assertEquals(propertyRef, readResponse.getBody().get(0).getProperty());

            RecordedRequest readRequest = mockWebServer.takeRequest();
            HttpUrl readUrl = readRequest.getRequestUrl();
            assertNotNull(readUrl);
            assertEquals("GET", readRequest.getMethod());
            assertEquals("/nipc/devices/" + deviceId + "/properties", readUrl.encodedPath());
            assertEquals(propertyRef, readUrl.queryParameter("propertyName"));

            NipcResponse<List<PropertyWriteResult>> writeResponse = controlClient.writeProperty(deviceId, propertyRef, "dGVzdA==");
            assertTrue(writeResponse.isSuccess(), String.valueOf(writeResponse.getError()));
            assertNotNull(writeResponse.getBody());
            assertEquals(200, writeResponse.getBody().get(0).getStatus());

            RecordedRequest writeRequest = mockWebServer.takeRequest();
            assertEquals("PUT", writeRequest.getMethod());
            assertEquals("/nipc/devices/" + deviceId + "/properties", writeRequest.getPath());
        } finally {
            mockWebServer.shutdown();
        }
    }

    @Test
    void propertyWriteResultProblemTypeEnum() throws Exception {
        MockWebServer mockWebServer = new MockWebServer();
        mockWebServer.start();
        try {
            String deviceId = UUID.randomUUID().toString();
            String propertyRef = "https://example.com/thermometer#/sdfObject/healthsensor/sdfProperty/readOnlyValue";
            String problemType = "https://www.iana.org/assignments/nipc-problem-types#property-not-writable";

            mockWebServer.enqueue(new MockResponse().setResponseCode(200)
                    .setBody("[{" +
                            "\"status\":403," +
                            "\"type\":\"" + problemType + "\"," +
                            "\"title\":\"Property not writable\"," +
                            "\"detail\":\"Property is read-only\"" +
                            "}]"));

            ControlClient controlClient = createControlClient(mockWebServer);

            NipcResponse<List<PropertyWriteResult>> response = controlClient.writeProperty(deviceId, propertyRef, "dGVzdA==");
            assertTrue(response.isSuccess(), String.valueOf(response.getError()));
            assertNotNull(response.getBody());
            assertEquals(1, response.getBody().size());
            assertEquals(403, response.getBody().get(0).getStatus());
            assertEquals(NipcProblemType.PROPERTY_NOT_WRITABLE, response.getBody().get(0).getType());
            assertEquals("Property not writable", response.getBody().get(0).getTitle());
            assertEquals("Property is read-only", response.getBody().get(0).getDetail());
        } finally {
            mockWebServer.shutdown();
        }
    }

    @Test
    void modelRegistrationApis() throws Exception {
        MockWebServer mockWebServer = new MockWebServer();
        mockWebServer.start();
        try {
            String sdfName = "https://example.com/thermometer#/sdfObject/healthsensor";
            SdfModel model = createComplexSdfModel();
            String modelJson = MAPPER.writeValueAsString(model);

            mockWebServer.enqueue(new MockResponse().setResponseCode(200).setBody("[{\"sdfName\":\"" + sdfName + "\"}]"));
            mockWebServer.enqueue(new MockResponse().setResponseCode(200).setBody("{\"sdfName\":\"" + sdfName + "\"}"));
            mockWebServer.enqueue(new MockResponse().setResponseCode(200).setBody("[{\"sdfName\":\"" + sdfName + "\"}]"));
            mockWebServer.enqueue(new MockResponse().setResponseCode(200).setBody(modelJson));
            mockWebServer.enqueue(new MockResponse().setResponseCode(200).setBody("{\"sdfName\":\"" + sdfName + "\"}"));

            ControlClient controlClient = createControlClient(mockWebServer);

            NipcResponse<List<ModelRegistrationResponse>> register = controlClient.registerSdfModel(model);
            assertTrue(register.isSuccess(), String.valueOf(register.getError()));
            assertNotNull(register.getBody());
            assertEquals(sdfName, register.getBody().get(0).getSdfName());

            RecordedRequest registerRequest = mockWebServer.takeRequest();
            assertEquals("POST", registerRequest.getMethod());
            assertEquals("/nipc/registrations/models", registerRequest.getPath());
            assertTrue(registerRequest.getHeader("Content-Type").startsWith("application/sdf+json"));
            assertJsonEquals(modelJson, registerRequest.getBody().readUtf8());

            NipcResponse<ModelRegistrationResponse> update = controlClient.updateSdfModel(sdfName, model);
            assertTrue(update.isSuccess(), String.valueOf(update.getError()));
            assertNotNull(update.getBody());
            assertEquals(sdfName, update.getBody().getSdfName());

            RecordedRequest updateRequest = mockWebServer.takeRequest();
            HttpUrl updateUrl = updateRequest.getRequestUrl();
            assertNotNull(updateUrl);
            assertEquals("PUT", updateRequest.getMethod());
            assertEquals("/nipc/registrations/models", updateUrl.encodedPath());
            assertEquals(sdfName, updateUrl.queryParameter("sdfName"));
            assertTrue(updateRequest.getHeader("Content-Type").startsWith("application/sdf+json"));
            assertJsonEquals(modelJson, updateRequest.getBody().readUtf8());

            NipcResponse<List<ModelRegistrationResponse>> allModels = controlClient.getSdfModels();
            assertTrue(allModels.isSuccess(), String.valueOf(allModels.getError()));
            RecordedRequest allModelsRequest = mockWebServer.takeRequest();
            assertEquals("GET", allModelsRequest.getMethod());
            assertEquals("/nipc/registrations/models", allModelsRequest.getPath());

            NipcResponse<SdfModel> oneModel = controlClient.getSdfModel(sdfName);
            assertTrue(oneModel.isSuccess(), String.valueOf(oneModel.getError()));
            assertNotNull(oneModel.getBody());
            assertEquals("thermometer", oneModel.getBody().getDefaultNamespace());
            assertNotNull(oneModel.getBody().getSdfObject());
            assertTrue(oneModel.getBody().getSdfObject().containsKey("healthsensor"));
            RecordedRequest oneModelRequest = mockWebServer.takeRequest();
            HttpUrl oneModelUrl = oneModelRequest.getRequestUrl();
            assertNotNull(oneModelUrl);
            assertEquals("GET", oneModelRequest.getMethod());
            assertEquals("/nipc/registrations/models", oneModelUrl.encodedPath());
            assertEquals(sdfName, oneModelUrl.queryParameter("sdfName"));

            NipcResponse<ModelRegistrationResponse> delete = controlClient.unregisterSdfModel(sdfName);
            assertTrue(delete.isSuccess(), String.valueOf(delete.getError()));
            assertNotNull(delete.getBody());
            assertEquals(sdfName, delete.getBody().getSdfName());
            RecordedRequest deleteRequest = mockWebServer.takeRequest();
            HttpUrl deleteUrl = deleteRequest.getRequestUrl();
            assertNotNull(deleteUrl);
            assertEquals("DELETE", deleteRequest.getMethod());
            assertEquals("/nipc/registrations/models", deleteUrl.encodedPath());
            assertEquals(sdfName, deleteUrl.queryParameter("sdfName"));
        } finally {
            mockWebServer.shutdown();
        }
    }

    @Test
    void dataAppApis() throws Exception {
        MockWebServer mockWebServer = new MockWebServer();
        mockWebServer.start();
        try {
            String dataAppId = UUID.randomUUID().toString();
            String eventRef = "https://example.com/thermometer#/sdfObject/healthsensor/sdfEvent/isPresent";

            mockWebServer.enqueue(new MockResponse().setResponseCode(200)
                    .setBody("{\"events\":[{\"event\":\"" + eventRef + "\"}],\"mqttClient\":true}"));
            mockWebServer.enqueue(new MockResponse().setResponseCode(200)
                    .setBody("{\"events\":[{\"event\":\"" + eventRef + "\"}],\"mqttClient\":true}"));
            mockWebServer.enqueue(new MockResponse().setResponseCode(200)
                    .setBody("{\"events\":[{\"event\":\"" + eventRef + "\"}],\"mqttClient\":true}"));
            mockWebServer.enqueue(new MockResponse().setResponseCode(200)
                    .setBody("{\"events\":[{\"event\":\"" + eventRef + "\"}],\"mqttClient\":true}"));

            ControlClient controlClient = createControlClient(mockWebServer);

            DataAppRegistration registration = new DataAppRegistration();
            Event event = new Event();
            event.setEvent(eventRef);
            registration.setEvents(List.of(event));
            registration.setMqttClient(true);

            NipcResponse<DataAppRegistration> create = controlClient.createDataApp(dataAppId, registration);
            assertTrue(create.isSuccess(), String.valueOf(create.getError()));
            assertNotNull(create.getBody());
            assertTrue(create.getBody().getMqttClient());
            RecordedRequest createRequest = mockWebServer.takeRequest();
            HttpUrl createUrl = createRequest.getRequestUrl();
            assertNotNull(createUrl);
            assertEquals("POST", createRequest.getMethod());
            assertEquals("/nipc/registrations/data-apps", createUrl.encodedPath());
            assertEquals(dataAppId, createUrl.queryParameter("dataAppId"));

            NipcResponse<DataAppRegistration> update = controlClient.updateDataApp(dataAppId, registration);
            assertTrue(update.isSuccess(), String.valueOf(update.getError()));
            RecordedRequest updateRequest = mockWebServer.takeRequest();
            HttpUrl updateUrl = updateRequest.getRequestUrl();
            assertNotNull(updateUrl);
            assertEquals("PUT", updateRequest.getMethod());
            assertEquals("/nipc/registrations/data-apps", updateUrl.encodedPath());
            assertEquals(dataAppId, updateUrl.queryParameter("dataAppId"));

            NipcResponse<DataAppRegistration> get = controlClient.getDataApp(dataAppId);
            assertTrue(get.isSuccess(), String.valueOf(get.getError()));
            RecordedRequest getRequest = mockWebServer.takeRequest();
            HttpUrl getUrl = getRequest.getRequestUrl();
            assertNotNull(getUrl);
            assertEquals("GET", getRequest.getMethod());
            assertEquals("/nipc/registrations/data-apps", getUrl.encodedPath());
            assertEquals(dataAppId, getUrl.queryParameter("dataAppId"));

            NipcResponse<DataAppRegistration> delete = controlClient.deleteDataApp(dataAppId);
            assertTrue(delete.isSuccess(), String.valueOf(delete.getError()));
            RecordedRequest deleteRequest = mockWebServer.takeRequest();
            HttpUrl deleteUrl = deleteRequest.getRequestUrl();
            assertNotNull(deleteUrl);
            assertEquals("DELETE", deleteRequest.getMethod());
            assertEquals("/nipc/registrations/data-apps", deleteUrl.encodedPath());
            assertEquals(dataAppId, deleteUrl.queryParameter("dataAppId"));
        } finally {
            mockWebServer.shutdown();
        }
    }

    @Test
    void eventApis() throws Exception {
        MockWebServer mockWebServer = new MockWebServer();
        mockWebServer.start();
        try {
            String deviceId = UUID.randomUUID().toString();
            String eventRef = "https://example.com/thermometer#/sdfObject/healthsensor/sdfEvent/isPresent";
            String instanceId = UUID.randomUUID().toString();

            mockWebServer.enqueue(new MockResponse()
                    .setResponseCode(200)
                    .setHeader("Location", "https://example.com/nipc/devices/" + deviceId + "/events?instanceId=" + instanceId));
            mockWebServer.enqueue(new MockResponse().setResponseCode(200));
            mockWebServer.enqueue(new MockResponse().setResponseCode(200)
                    .setBody("[{\"event\":\"" + eventRef + "\",\"instanceId\":\"" + instanceId + "\"}]"));
            mockWebServer.enqueue(new MockResponse().setResponseCode(200)
                    .setBody("[{\"event\":\"" + eventRef + "\",\"instanceId\":\"" + instanceId + "\"}]"));

            ControlClient controlClient = createControlClient(mockWebServer);

            NipcResponse<String> enable = controlClient.enableEvent(deviceId, eventRef);
            assertTrue(enable.isSuccess(), String.valueOf(enable.getError()));
            assertEquals(instanceId, enable.getBody());
            RecordedRequest enableRequest = mockWebServer.takeRequest();
            HttpUrl enableUrl = enableRequest.getRequestUrl();
            assertNotNull(enableUrl);
            assertEquals(eventRef, enableUrl.queryParameter("eventName"));

            NipcResponse<Void> disable = controlClient.disableEvent(deviceId, instanceId);
            assertTrue(disable.isSuccess(), String.valueOf(disable.getError()));
            RecordedRequest disableRequest = mockWebServer.takeRequest();
            HttpUrl disableUrl = disableRequest.getRequestUrl();
            assertNotNull(disableUrl);
            assertEquals("DELETE", disableRequest.getMethod());
            assertEquals("/nipc/devices/" + deviceId + "/events", disableUrl.encodedPath());
            assertEquals(instanceId, disableUrl.queryParameter("instanceId"));

            NipcResponse<List<TiedieEventResponse>> one = controlClient.getEvent(deviceId, instanceId);
            assertTrue(one.isSuccess(), String.valueOf(one.getError()));
            assertNotNull(one.getBody());
            assertEquals(instanceId, one.getBody().get(0).getInstanceId());
            RecordedRequest oneRequest = mockWebServer.takeRequest();
            HttpUrl oneUrl = oneRequest.getRequestUrl();
            assertNotNull(oneUrl);
            assertEquals("GET", oneRequest.getMethod());
            assertEquals("/nipc/devices/" + deviceId + "/events", oneUrl.encodedPath());
            assertEquals(instanceId, oneUrl.queryParameter("instanceId"));

            NipcResponse<List<TiedieEventResponse>> all = controlClient.getAllEvents(deviceId);
            assertTrue(all.isSuccess(), String.valueOf(all.getError()));
            assertNotNull(all.getBody());
            assertEquals(1, all.getBody().size());
            RecordedRequest allRequest = mockWebServer.takeRequest();
            assertEquals("GET", allRequest.getMethod());
            assertEquals("/nipc/devices/" + deviceId + "/events", allRequest.getPath());
        } finally {
            mockWebServer.shutdown();
        }
    }

    @Test
    void apiKeyHeader() throws Exception {
        MockWebServer mockWebServer = new MockWebServer();
        mockWebServer.start();
        try {
            mockWebServer.enqueue(new MockResponse().setResponseCode(200)
                    .setBody("{" +
                            "\"sdfProtocolMap\":{\"ble\":[{" +
                            "\"serviceID\":\"1800\"," +
                            "\"characteristics\":[{" +
                            "\"characteristicID\":\"2a00\",\"flags\":[\"read\"]" +
                            "}]" +
                            "}]}}"));

            ControlClient controlClient = createControlClient(mockWebServer);
            String deviceId = UUID.randomUUID().toString();

            NipcResponse<List<DataParameter>> response = controlClient.connect(createBleDevice(deviceId));
            assertTrue(response.isSuccess(), String.valueOf(response.getError()));

            RecordedRequest request = mockWebServer.takeRequest();
            assertEquals(CONTROL_API_KEY, request.getHeader("x-api-key"));
        } finally {
            mockWebServer.shutdown();
        }
    }
}
