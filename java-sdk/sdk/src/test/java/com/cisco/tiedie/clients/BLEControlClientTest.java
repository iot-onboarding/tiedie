// Copyright (c) 2023, Cisco and/or its affiliates.
// All rights reserved.
// See LICENSE file in this distribution.
// SPDX-License-Identifier: Apache-2.0

package com.cisco.tiedie.clients;

import com.cisco.tiedie.dto.control.*;
import com.cisco.tiedie.dto.control.ble.BleConnectRequest;
import com.cisco.tiedie.dto.control.ble.BleDataParameter;
import com.cisco.tiedie.dto.control.ble.BleService;
import com.cisco.tiedie.dto.scim.BleExtension;
import com.cisco.tiedie.dto.scim.Device;
import okhttp3.mockwebserver.MockResponse;
import okhttp3.mockwebserver.RecordedRequest;
import org.junit.jupiter.api.Disabled;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.MethodSource;

import java.util.Arrays;
import java.util.List;
import java.util.UUID;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertInstanceOf;

class BLEControlClientTest extends ControlClientTest {
    @Disabled("Operation not supported in BLE")
    @Override
    public void introduce(ControlClient controlClient) {
    }

    @MethodSource("clientProvider")
    @DisplayName("connect")
    @ParameterizedTest(name = "{0}")
    public void connect(ControlClient controlClient) throws Exception {
        var mockResponse = new MockResponse()
                .setResponseCode(200)
                .setBody("{\n" +
                        "    \"status\" : \"SUCCESS\",\n" +
                        "    \"services\" : [\n" +
                        "        {\n" +
                        "            \"serviceID\" : \"1800\",\n" +
                        "            \"characteristics\" : [\n" +
                        "                {\n" +
                        "                    \"characteristicID\" : \"2a00\",\n" +
                        "                    \"flags\" : [\n" +
                        "                        \"read\",\n" +
                        "                        \"write\"\n" +
                        "                    ],\n" +
                        "                    \"descriptors\" : [\n" +
                        "                        {\n" +
                        "                            \"descriptorID\": \"2a10\"\n" +
                        "                        }\n" +
                        "                    ]\n" +
                        "                },\n" +
                        "                {\n" +
                        "                    \"characteristicID\" : \"2a01\",\n" +
                        "                    \"flags\" : [\n" +
                        "                        \"read\"\n" +
                        "                    ],\n" +
                        "                    \"descriptors\" : [\n" +
                        "                        {\n" +
                        "                            \"descriptorID\": \"2a11\"\n" +
                        "                        }\n" +
                        "                    ]\n" +
                        "                },\n" +
                        "                {\n" +
                        "                    \"characteristicID\" : \"2a04\",\n" +
                        "                    \"flags\" : [\n" +
                        "                        \"read\",\n" +
                        "                        \"notify\"\n" +
                        "                    ],\n" +
                        "                    \"descriptors\" : [\n" +
                        "                        {\n" +
                        "                            \"descriptorID\": \"2a14\"\n" +
                        "                        }\n" +
                        "                    ]\n" +
                        "                },\n" +
                        "                {\n" +
                        "                    \"characteristicID\" : \"2aa6\",\n" +
                        "                    \"flags\" : [\n" +
                        "                        \"read\"\n" +
                        "                    ],\n" +
                        "                    \"descriptors\" : [\n" +
                        "                        {\n" +
                        "                            \"descriptorID\": \"2a16\"\n" +
                        "                        }\n" +
                        "                    ]\n" +
                        "                }\n" +
                        "            ]\n" +
                        "        }\n" +
                        "    ]\n" +
                        "}");
        mockWebServer.enqueue(mockResponse);
        mockWebServer.enqueue(mockResponse);
        mockWebServer.enqueue(mockResponse);
        mockWebServer.enqueue(mockResponse);
        mockWebServer.enqueue(new MockResponse()
                .setResponseCode(400)
                .setBody("{\n" +
                        "  \"status\": \"FAILURE\",\n" +
                        "  \"reason\": \"Connect failed\",\n" +
                        "  \"errorCode\": 1\n" +
                        "}"));

        var deviceId = UUID.randomUUID().toString();

        var device = Device.builder()
                .id(deviceId)
                .deviceDisplayName("BLE Monitor")
                .adminState(false)
                .bleExtension(BleExtension.builder()
                        .deviceMacAddress("AA:BB:CC:11:22:33")
                        .isRandom(false)
                        .versionSupport(Arrays.asList("4.1", "4.2", "5.0", "5.1", "5.2", "5.3"))
                        .pairingPassKey(new BleExtension.PairingPassKey(123456))
                        .build())
                .build();

        TiedieResponse<List<DataParameter>> response = controlClient.connect(device);

        assertEquals(200, response.getHttpStatusCode());
        assertEquals("OK", response.getHttpMessage());
        assertEquals(TiedieStatus.SUCCESS, response.getStatus());

        var expectedParameters = Arrays.asList(
                new String[] { "1800", "2a00" },
                new String[] { "1800", "2a01" },
                new String[] { "1800", "2a04" },
                new String[] { "1800", "2aa6" });
        var expectedFlags = Arrays.asList(
                Arrays.asList("read", "write"),
                List.of("read"),
                List.of("read", "notify"),
                List.of("read"));
        List<DataParameter> body = response.getBody();

        for (int i = 0; i < body.size(); i++) {
            DataParameter dataParameter = body.get(i);
            assertInstanceOf(BleDataParameter.class, dataParameter);
            BleDataParameter bleDataParameter = (BleDataParameter) dataParameter;

            BleDataParameter expected = new BleDataParameter();

            expected.setDeviceId(deviceId);
            expected.setServiceUUID(expectedParameters.get(i)[0]);
            expected.setCharUUID(expectedParameters.get(i)[1]);
            expected.setFlags(expectedFlags.get(i));

            assertEquals(expected, bleDataParameter);
        }

        RecordedRequest request = mockWebServer.takeRequest();
        assertEquals("/control/connectivity/connect", request.getPath());
        assertEquals("POST", request.getMethod());
        assertEquals("{\n" +
                "  \"technology\" : \"ble\",\n" +
                "  \"id\" : \"" + deviceId + "\",\n" +
                "  \"controlApp\" : \"" + CONTROL_APP_ID + "\",\n" +
                "  \"ble\" : {\n" +
                "    \"retries\" : 3,\n" +
                "    \"retryMultipleAPs\" : true\n" +
                "  }\n" +
                "}", request.getBody().readUtf8());

        response = controlClient.connect(device,
                BleConnectRequest.builder()
                        .retries(5)
                        .retryMultipleAPs(false)
                        .build());

        assertEquals(200, response.getHttpStatusCode());
        assertEquals("OK", response.getHttpMessage());
        assertEquals(TiedieStatus.SUCCESS, response.getStatus());

        request = mockWebServer.takeRequest();
        assertEquals("/control/connectivity/connect", request.getPath());
        assertEquals("POST", request.getMethod());
        assertEquals("{\n" +
                "  \"technology\" : \"ble\",\n" +
                "  \"id\" : \"" + deviceId + "\",\n" +
                "  \"controlApp\" : \"" + CONTROL_APP_ID + "\",\n" +
                "  \"ble\" : {\n" +
                "    \"retries\" : 5,\n" +
                "    \"retryMultipleAPs\" : false\n" +
                "  }\n" +
                "}", request.getBody().readUtf8());

        response = controlClient.connect(device,
                BleConnectRequest
                        .builder()
                        .services(List.of(new BleService("1800")))
                        .build());

        assertEquals(200, response.getHttpStatusCode());
        assertEquals("OK", response.getHttpMessage());
        assertEquals(TiedieStatus.SUCCESS, response.getStatus());

        request = mockWebServer.takeRequest();
        assertEquals("/control/connectivity/connect", request.getPath());
        assertEquals("POST", request.getMethod());
        assertEquals("{\n" +
                "  \"technology\" : \"ble\",\n" +
                "  \"id\" : \"" + deviceId + "\",\n" +
                "  \"controlApp\" : \"" + CONTROL_APP_ID + "\",\n" +
                "  \"ble\" : {\n" +
                "    \"services\" : [ {\n" +
                "      \"serviceID\" : \"1800\"\n" +
                "    } ],\n" +
                "    \"retries\" : 3,\n" +
                "    \"retryMultipleAPs\" : false\n" +
                "  }\n" +
                "}", request.getBody().readUtf8());

        response = controlClient.connect(device, BleConnectRequest
                .builder()
                .services(List.of(new BleService("1800")))
                .retries(5)
                .retryMultipleAPs(true)
                .build());

        assertEquals(200, response.getHttpStatusCode());
        assertEquals("OK", response.getHttpMessage());
        assertEquals(TiedieStatus.SUCCESS, response.getStatus());

        request = mockWebServer.takeRequest();
        assertEquals("/control/connectivity/connect", request.getPath());
        assertEquals("POST", request.getMethod());
        assertEquals("{\n" +
                "  \"technology\" : \"ble\",\n" +
                "  \"id\" : \"" + deviceId + "\",\n" +
                "  \"controlApp\" : \"" + CONTROL_APP_ID + "\",\n" +
                "  \"ble\" : {\n" +
                "    \"services\" : [ {\n" +
                "      \"serviceID\" : \"1800\"\n" +
                "    } ],\n" +
                "    \"retries\" : 5,\n" +
                "    \"retryMultipleAPs\" : true\n" +
                "  }\n" +
                "}", request.getBody().readUtf8());

        response = controlClient.connect(device,
                BleConnectRequest.builder()
                        .retries(5)
                        .retryMultipleAPs(false)
                        .build());
        assertEquals(400, response.getHttpStatusCode());
        assertEquals(TiedieStatus.FAILURE, response.getStatus());
        assertEquals("Connect failed", response.getReason());
        assertEquals(1, response.getErrorCode());

        request = mockWebServer.takeRequest();
        assertEquals("/control/connectivity/connect", request.getPath());
        assertEquals("POST", request.getMethod());
    }

    @MethodSource("clientProvider")
    @DisplayName("disconnect")
    @ParameterizedTest(name = "{0}")
    public void disconnect(ControlClient controlClient) throws Exception {
        mockWebServer.enqueue(new MockResponse()
                .setResponseCode(200)
                .setBody("{\"status\": \"SUCCESS\"}"));

        var deviceId = UUID.randomUUID().toString();

        var device = Device.builder()
                .id(deviceId)
                .deviceDisplayName("BLE Monitor")
                .adminState(false)
                .bleExtension(BleExtension.builder()
                        .deviceMacAddress("AA:BB:CC:11:22:33")
                        .isRandom(false)
                        .versionSupport(Arrays.asList("4.1", "4.2", "5.0", "5.1", "5.2", "5.3"))
                        .pairingPassKey(new BleExtension.PairingPassKey(123456))
                        .build())
                .build();

        TiedieResponse<Void> response = controlClient.disconnect(device);

        assertEquals(200, response.getHttpStatusCode());
        assertEquals("OK", response.getHttpMessage());
        assertEquals(TiedieStatus.SUCCESS, response.getStatus());

        var request = mockWebServer.takeRequest();
        assertEquals("/control/connectivity/disconnect", request.getPath());
        assertEquals("POST", request.getMethod());

        assertEquals("{\n" +
                "  \"technology\" : \"ble\",\n" +
                "  \"id\" : \"" + deviceId + "\",\n" +
                "  \"controlApp\" : \"" + CONTROL_APP_ID + "\"\n" +
                "}", request.getBody().readUtf8());
    }

    @MethodSource("clientProvider")
    @DisplayName("discover")
    @ParameterizedTest(name = "{0}")
    public void discover(ControlClient controlClient) throws Exception {
        var mockResponse = new MockResponse()
                .setResponseCode(200)
                .setBody("{\n" +
                        "    \"status\" : \"SUCCESS\",\n" +
                        "    \"services\" : [\n" +
                        "        {\n" +
                        "            \"serviceID\" : \"1800\",\n" +
                        "            \"characteristics\" : [\n" +
                        "                {\n" +
                        "                    \"characteristicID\" : \"2a00\",\n" +
                        "                    \"flags\" : [\n" +
                        "                        \"read\",\n" +
                        "                        \"write\"\n" +
                        "                    ],\n" +
                        "                    \"descriptors\" : [\n" +
                        "                        {\n" +
                        "                            \"descriptorID\": \"2a10\"\n" +
                        "                        }\n" +
                        "                    ]\n" +
                        "                },\n" +
                        "                {\n" +
                        "                    \"characteristicID\" : \"2a01\",\n" +
                        "                    \"flags\" : [\n" +
                        "                        \"read\"\n" +
                        "                    ],\n" +
                        "                    \"descriptors\" : [\n" +
                        "                        {\n" +
                        "                            \"descriptorID\": \"2a11\"\n" +
                        "                        }\n" +
                        "                    ]\n" +
                        "                },\n" +
                        "                {\n" +
                        "                    \"characteristicID\" : \"2a04\",\n" +
                        "                    \"flags\" : [\n" +
                        "                        \"read\",\n" +
                        "                        \"notify\"\n" +
                        "                    ],\n" +
                        "                    \"descriptors\" : [\n" +
                        "                        {\n" +
                        "                            \"descriptorID\": \"2a14\"\n" +
                        "                        }\n" +
                        "                    ]\n" +
                        "                },\n" +
                        "                {\n" +
                        "                    \"characteristicID\" : \"2aa6\",\n" +
                        "                    \"flags\" : [\n" +
                        "                        \"read\"\n" +
                        "                    ],\n" +
                        "                    \"descriptors\" : [\n" +
                        "                        {\n" +
                        "                            \"descriptorID\": \"2a16\"\n" +
                        "                        }\n" +
                        "                    ]\n" +
                        "                }\n" +
                        "            ]\n" +
                        "        }\n" +
                        "    ]\n" +
                        "}");
        mockWebServer.enqueue(mockResponse);

        var deviceId = UUID.randomUUID().toString();

        var device = Device.builder()
                .id(deviceId)
                .deviceDisplayName("BLE Monitor")
                .adminState(false)
                .bleExtension(BleExtension.builder()
                        .deviceMacAddress("AA:BB:CC:11:22:33")
                        .isRandom(false)
                        .versionSupport(Arrays.asList("4.1", "4.2", "5.0", "5.1", "5.2", "5.3"))
                        .pairingPassKey(new BleExtension.PairingPassKey(123456))
                        .build())
                .build();

        TiedieResponse<List<DataParameter>> response = controlClient.discover(device, List.of(new BleDataParameter("1800")));

        assertEquals(200, response.getHttpStatusCode());
        assertEquals("OK", response.getHttpMessage());
        assertEquals(TiedieStatus.SUCCESS, response.getStatus());

        var expectedParameters = Arrays.asList(
                new String[] { "1800", "2a00" },
                new String[] { "1800", "2a01" },
                new String[] { "1800", "2a04" },
                new String[] { "1800", "2aa6" });
        var expectedFlags = Arrays.asList(
                Arrays.asList("read", "write"),
                List.of("read"),
                List.of("read", "notify"),
                List.of("read"));
        List<DataParameter> body = response.getBody();

        for (int i = 0; i < body.size(); i++) {
            DataParameter dataParameter = body.get(i);
            assertInstanceOf(BleDataParameter.class, dataParameter);
            BleDataParameter bleDataParameter = (BleDataParameter) dataParameter;

            BleDataParameter expected = new BleDataParameter();

            expected.setDeviceId(deviceId);
            expected.setServiceUUID(expectedParameters.get(i)[0]);
            expected.setCharUUID(expectedParameters.get(i)[1]);
            expected.setFlags(expectedFlags.get(i));

            assertEquals(expected, bleDataParameter);
        }

        RecordedRequest request = mockWebServer.takeRequest();
        assertEquals("/control/data/discover", request.getPath());
        assertEquals("POST", request.getMethod());
        assertEquals("{\n" +
                "  \"technology\" : \"ble\",\n" +
                "  \"id\" : \"" + deviceId + "\",\n" +
                "  \"controlApp\" : \"" + CONTROL_APP_ID + "\",\n" +
                "  \"ble\" : {\n" + //
                "    \"services\" : [ {\n" + //
                "      \"serviceID\" : \"1800\"\n" + //
                "    } ]\n" + //
                "  }\n" +
                "}", request.getBody().readUtf8());
    }

    @MethodSource("clientProvider")
    @DisplayName("read")
    @ParameterizedTest(name = "{0}")
    public void read(ControlClient controlClient) throws Exception {
        var mockResponse = new MockResponse()
                .setResponseCode(200)
                .setBody("{\n" +
                        "  \"status\": \"SUCCESS\",\n" +
                        "  \"value\": \"0001\"\n" +
                        "}");
        mockWebServer.enqueue(mockResponse);

        var deviceId = UUID.randomUUID().toString();

        var bleDataParameter = new BleDataParameter(deviceId, "1800", "2a00");

        TiedieResponse<DataResponse> response = controlClient.read(bleDataParameter);

        assertEquals(200, response.getHttpStatusCode());
        assertEquals("OK", response.getHttpMessage());
        assertEquals(TiedieStatus.SUCCESS, response.getStatus());

        RecordedRequest request = mockWebServer.takeRequest();
        assertEquals("/control/data/read", request.getPath());
        assertEquals("POST", request.getMethod());
        assertEquals("{\n" +
                "  \"technology\" : \"ble\",\n" +
                "  \"id\" : \"" + deviceId + "\",\n" +
                "  \"controlApp\" : \"control-app\",\n" +
                "  \"ble\" : {\n" +
                "    \"serviceID\" : \"1800\",\n" +
                "    \"characteristicID\" : \"2a00\"\n" +
                "  }\n" +
                "}", request.getBody().readUtf8());
    }

    @MethodSource("clientProvider")
    @DisplayName("write")
    @ParameterizedTest(name = "{0}")
    public void write(ControlClient controlClient) throws Exception {
        String value = "0001";
        var mockResponse = new MockResponse()
                .setResponseCode(200)
                .setBody("{\n" +
                        "  \"status\": \"SUCCESS\",\n" +
                        "  \"value\": \"" + value + "\"\n" +
                        "}");
        mockWebServer.enqueue(mockResponse);

        var deviceId = UUID.randomUUID().toString();

        var bleDataParameter = new BleDataParameter(deviceId, "1800", "2a00");

        TiedieResponse<DataResponse> response = controlClient.write(bleDataParameter, value);

        assertEquals(200, response.getHttpStatusCode());
        assertEquals("OK", response.getHttpMessage());
        assertEquals(TiedieStatus.SUCCESS, response.getStatus());
        assertEquals(value, response.getBody().getValue());

        RecordedRequest request = mockWebServer.takeRequest();
        assertEquals("/control/data/write", request.getPath());
        assertEquals("POST", request.getMethod());
        assertEquals("{\n" +
                "  \"technology\" : \"ble\",\n" +
                "  \"id\" : \"" + deviceId + "\",\n" +
                "  \"controlApp\" : \"control-app\",\n" +
                "  \"value\" : \"" + value + "\",\n" +
                "  \"ble\" : {\n" +
                "    \"serviceID\" : \"1800\",\n" +
                "    \"characteristicID\" : \"2a00\"\n" +
                "  }\n" +
                "}", request.getBody().readUtf8());
    }

    @MethodSource("clientProvider")
    @DisplayName("subscribe")
    @ParameterizedTest(name = "{0}")
    public void subscribe(ControlClient controlClient) throws Exception {
        var mockResponse = new MockResponse()
                .setResponseCode(200)
                .setBody("{\n" +
                        "  \"status\": \"SUCCESS\"\n" +
                        "}");
        mockWebServer.enqueue(mockResponse);
        mockWebServer.enqueue(mockResponse);

        var deviceId = UUID.randomUUID().toString();

        var bleDataParameter = new BleDataParameter(deviceId, "1800", "2a00");

        TiedieResponse<Void> response = controlClient.subscribe(bleDataParameter);

        assertEquals(200, response.getHttpStatusCode());
        assertEquals("OK", response.getHttpMessage());
        assertEquals(TiedieStatus.SUCCESS, response.getStatus());

        RecordedRequest request = mockWebServer.takeRequest();
        assertEquals("/control/data/subscribe", request.getPath());
        assertEquals("POST", request.getMethod());
        assertEquals("{\n" +
                "  \"technology\" : \"ble\",\n" +
                "  \"id\" : \"" + deviceId + "\",\n" +
                "  \"controlApp\" : \"control-app\",\n" +
                "  \"dataFormat\" : \"default\",\n" +
                "  \"ble\" : {\n" +
                "    \"serviceID\" : \"1800\",\n" +
                "    \"characteristicID\" : \"2a00\"\n" +
                "  }\n" +
                "}", request.getBody().readUtf8());

        SubscriptionOptions options = SubscriptionOptions.builder()
                .topic("enterprise/hospital/pulse_oximeter")
                .dataFormat(DataFormat.PAYLOAD)
                .build();
        response = controlClient.subscribe(bleDataParameter, options);

        assertEquals(200, response.getHttpStatusCode());
        assertEquals("OK", response.getHttpMessage());
        assertEquals(TiedieStatus.SUCCESS, response.getStatus());

        request = mockWebServer.takeRequest();
        assertEquals("/control/data/subscribe", request.getPath());
        assertEquals("POST", request.getMethod());
        assertEquals("{\n" +
                "  \"technology\" : \"ble\",\n" +
                "  \"id\" : \"" + deviceId + "\",\n" +
                "  \"controlApp\" : \"control-app\",\n" +
                "  \"topic\" : \"enterprise/hospital/pulse_oximeter\",\n" +
                "  \"dataFormat\" : \"payload\",\n" +
                "  \"ble\" : {\n" +
                "    \"serviceID\" : \"1800\",\n" +
                "    \"characteristicID\" : \"2a00\"\n" +
                "  }\n" +
                "}", request.getBody().readUtf8());
    }

    @MethodSource("clientProvider")
    @DisplayName("unsubscribe")
    @ParameterizedTest(name = "{0}")
    public void unsubscribe(ControlClient controlClient) throws Exception {
        var mockResponse = new MockResponse()
                .setResponseCode(200)
                .setBody("{\n" +
                        "  \"status\": \"SUCCESS\"\n" +
                        "}");
        mockWebServer.enqueue(mockResponse);

        var deviceId = UUID.randomUUID().toString();

        var bleDataParameter = new BleDataParameter(deviceId, "1800", "2a00");

        TiedieResponse<Void> response = controlClient.unsubscribe(bleDataParameter);

        assertEquals(200, response.getHttpStatusCode());
        assertEquals("OK", response.getHttpMessage());
        assertEquals(TiedieStatus.SUCCESS, response.getStatus());

        RecordedRequest request = mockWebServer.takeRequest();
        assertEquals("/control/data/unsubscribe", request.getPath());
        assertEquals("POST", request.getMethod());
        assertEquals("{\n" +
                "  \"technology\" : \"ble\",\n" +
                "  \"id\" : \"" + deviceId + "\",\n" +
                "  \"controlApp\" : \"control-app\",\n" +
                "  \"ble\" : {\n" +
                "    \"serviceID\" : \"1800\",\n" +
                "    \"characteristicID\" : \"2a00\"\n" +
                "  }\n" +
                "}", request.getBody().readUtf8());
    }
}