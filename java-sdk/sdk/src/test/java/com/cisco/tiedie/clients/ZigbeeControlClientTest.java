// Copyright (c) 2023, Cisco and/or its affiliates.
// All rights reserved.
// See license in distribution for details.

package com.cisco.tiedie.clients;

import com.cisco.tiedie.dto.control.*;
import com.cisco.tiedie.dto.control.zigbee.ZigbeeDataParameter;
import com.cisco.tiedie.dto.scim.Device;
import com.cisco.tiedie.dto.scim.ZigbeeExtension;
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

class ZigbeeControlClientTest extends ControlClientTest {

    @MethodSource("clientProvider")
    @DisplayName("introduce")
    @ParameterizedTest(name = "{0}")
    @Override
    public void introduce(ControlClient controlClient) throws Exception {
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
                "  \"uuid\" : \"" + deviceId + "\",\n" +
                "  \"controlApp\" : \"" + CONTROL_APP_ID + "\"\n" +
                "}", request.getBody().readUtf8());
    }

    @Disabled("Operation not supported in Zigbee")
    @Override
    public void connect(ControlClient controlClient) {

    }

    @Disabled("Operation not supported in Zigbee")
    @Override
    public void disconnect(ControlClient controlClient) {

    }

    @MethodSource("clientProvider")
    @DisplayName("discover")
    @ParameterizedTest(name = "{0}")
    public void discover(ControlClient controlClient) throws Exception {
        var mockResponse = new MockResponse()
                .setResponseCode(200)
                .setBody("{\n" +
                        "    \"status\": \"SUCCESS\",\n" +
                        "    \"endpoints\": [\n" +
                        "      {\n" +
                        "        \"endpointId\": 10,\n" +
                        "        \"clusters\": [\n" +
                        "          {\n" +
                        "            \"clusterId\": 0,\n" +
                        "            \"attributes\": [\n" +
                        "              {\n" +
                        "                \"attributeId\": 0,\n" +
                        "                \"attributeType\": 32\n" +
                        "              },\n" +
                        "              {\n" +
                        "                \"attributeId\": 1,\n" +
                        "                \"attributeType\": 32\n" +
                        "              }\n" +
                        "            ]\n" +
                        "          },\n" +
                        "          {\n" +
                        "            \"clusterId\": 3,\n" +
                        "            \"attributes\": [\n" +
                        "              {\n" +
                        "                \"attributeId\": 0,\n" +
                        "                \"attributeType\": 33\n" +
                        "              }\n" +
                        "            ]\n" +
                        "          }\n" +
                        "        ]\n" +
                        "      }\n" +
                        "    ]\n" +
                        "  }");
        mockWebServer.enqueue(mockResponse);

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

        TiedieResponse<List<DataParameter>> response = controlClient.discover(device);

        assertEquals(200, response.getHttpStatusCode());
        assertEquals("OK", response.getHttpMessage());
        assertEquals(TiedieStatus.SUCCESS, response.getStatus());

        var expectedParameters = Arrays.asList(
                new int[]{10, 0, 0, 32},
                new int[]{10, 0, 1, 32},
                new int[]{10, 3, 0, 33}
        );
        List<DataParameter> body = response.getBody();

        for (int i = 0; i < body.size(); i++) {
            DataParameter dataParameter = body.get(i);
            assertInstanceOf(ZigbeeDataParameter.class, dataParameter);
            ZigbeeDataParameter zigbeeDataParameter = (ZigbeeDataParameter) dataParameter;

            ZigbeeDataParameter expected = new ZigbeeDataParameter();

            expected.setDeviceId(deviceId);
            expected.setEndpointID(expectedParameters.get(i)[0]);
            expected.setClusterID(expectedParameters.get(i)[1]);
            expected.setAttributeID(expectedParameters.get(i)[2]);
            expected.setType(expectedParameters.get(i)[3]);

            assertEquals(expected, zigbeeDataParameter);
        }

        RecordedRequest request = mockWebServer.takeRequest();
        assertEquals("/control/data/discover", request.getPath());
        assertEquals("POST", request.getMethod());
        assertEquals("{\n" +
                "  \"technology\" : \"zigbee\",\n" +
                "  \"uuid\" : \"" + deviceId + "\",\n" +
                "  \"controlApp\" : \"" + CONTROL_APP_ID + "\"\n" +
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

        var zigbeeDataParameter = new ZigbeeDataParameter(deviceId, 1, 6, 0);

        TiedieResponse<DataResponse> response = controlClient.read(zigbeeDataParameter);

        assertEquals(200, response.getHttpStatusCode());
        assertEquals("OK", response.getHttpMessage());
        assertEquals(TiedieStatus.SUCCESS, response.getStatus());

        RecordedRequest request = mockWebServer.takeRequest();
        assertEquals("/control/data/read", request.getPath());
        assertEquals("POST", request.getMethod());
        assertEquals("{\n" +
                "  \"technology\" : \"zigbee\",\n" +
                "  \"uuid\" : \"" + deviceId + "\",\n" +
                "  \"controlApp\" : \"control-app\",\n" +
                "  \"zigbee\" : {\n" +
                "    \"endpointID\" : 1,\n" +
                "    \"clusterID\" : 6,\n" +
                "    \"attributeID\" : 0\n" +
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

        var zigbeeDataParameter = new ZigbeeDataParameter(deviceId, 1, 3, 0, 33);

        TiedieResponse<DataResponse> response = controlClient.write(zigbeeDataParameter, value);

        assertEquals(200, response.getHttpStatusCode());
        assertEquals("OK", response.getHttpMessage());
        assertEquals(TiedieStatus.SUCCESS, response.getStatus());

        RecordedRequest request = mockWebServer.takeRequest();
        assertEquals("/control/data/write", request.getPath());
        assertEquals("POST", request.getMethod());
        assertEquals("{\n" +
                "  \"technology\" : \"zigbee\",\n" +
                "  \"uuid\" : \"" + deviceId + "\",\n" +
                "  \"controlApp\" : \"control-app\",\n" +
                "  \"zigbee\" : {\n" +
                "    \"endpointID\" : 1,\n" +
                "    \"clusterID\" : 3,\n" +
                "    \"attributeID\" : 0,\n" +
                "    \"type\" : 33,\n" +
                "    \"data\" : [ 0, 1 ]\n" +
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
                        "  \"status\": \"SUCCESS\",\n" +
                        "  \"value\": \"0001\"\n" +
                        "}");
        mockWebServer.enqueue(mockResponse);
        mockWebServer.enqueue(mockResponse);

        var deviceId = UUID.randomUUID().toString();

        var zigbeeDataParameter = new ZigbeeDataParameter(deviceId, 1, 6, 0, 16);

        TiedieResponse<Void> response = controlClient.subscribe(zigbeeDataParameter);

        assertEquals(200, response.getHttpStatusCode());
        assertEquals("OK", response.getHttpMessage());
        assertEquals(TiedieStatus.SUCCESS, response.getStatus());

        RecordedRequest request = mockWebServer.takeRequest();
        assertEquals("/control/data/subscribe", request.getPath());
        assertEquals("POST", request.getMethod());
        assertEquals("{\n" +
                "  \"technology\" : \"zigbee\",\n" +
                "  \"uuid\" : \"" + deviceId + "\",\n" +
                "  \"controlApp\" : \"control-app\",\n" +
                "  \"dataFormat\" : \"default\",\n" +
                "  \"zigbee\" : {\n" +
                "    \"endpointID\" : 1,\n" +
                "    \"clusterID\" : 6,\n" +
                "    \"attributeID\" : 0,\n" +
                "    \"type\" : 16,\n" +
                "    \"minReportTime\" : 0,\n" +
                "    \"maxReportTime\" : 60\n" +
                "  }\n" +
                "}", request.getBody().readUtf8());

        response = controlClient.subscribe(zigbeeDataParameter, SubscriptionOptions.builder()
                        .minReportTime(5)
                        .maxReportTime(10)
                .build());

        assertEquals(200, response.getHttpStatusCode());
        assertEquals("OK", response.getHttpMessage());
        assertEquals(TiedieStatus.SUCCESS, response.getStatus());

        request = mockWebServer.takeRequest();
        assertEquals("/control/data/subscribe", request.getPath());
        assertEquals("POST", request.getMethod());
        assertEquals("{\n" +
                "  \"technology\" : \"zigbee\",\n" +
                "  \"uuid\" : \"" + deviceId + "\",\n" +
                "  \"controlApp\" : \"control-app\",\n" +
                "  \"dataFormat\" : \"default\",\n" +
                "  \"zigbee\" : {\n" +
                "    \"endpointID\" : 1,\n" +
                "    \"clusterID\" : 6,\n" +
                "    \"attributeID\" : 0,\n" +
                "    \"type\" : 16,\n" +
                "    \"minReportTime\" : 5,\n" +
                "    \"maxReportTime\" : 10\n" +
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
                        "  \"status\": \"SUCCESS\",\n" +
                        "  \"value\": \"0001\"\n" +
                        "}");
        mockWebServer.enqueue(mockResponse);

        var deviceId = UUID.randomUUID().toString();

        var zigbeeDataParameter = new ZigbeeDataParameter(deviceId, 1, 6, 0, 16);

        TiedieResponse<Void> response = controlClient.unsubscribe(zigbeeDataParameter);

        assertEquals(200, response.getHttpStatusCode());
        assertEquals("OK", response.getHttpMessage());
        assertEquals(TiedieStatus.SUCCESS, response.getStatus());

        RecordedRequest request = mockWebServer.takeRequest();
        assertEquals("/control/data/unsubscribe", request.getPath());
        assertEquals("POST", request.getMethod());
        assertEquals("{\n" +
                "  \"technology\" : \"zigbee\",\n" +
                "  \"uuid\" : \"" + deviceId + "\",\n" +
                "  \"controlApp\" : \"control-app\",\n" +
                "  \"zigbee\" : {\n" +
                "    \"endpointID\" : 1,\n" +
                "    \"clusterID\" : 6,\n" +
                "    \"attributeID\" : 0,\n" +
                "    \"type\" : 16\n" +
                "  }\n" +
                "}", request.getBody().readUtf8());
    }
}

