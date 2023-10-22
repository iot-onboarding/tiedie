// Copyright (c) 2023, Cisco and/or its affiliates.
// All rights reserved.
// See license in distribution for details.

package com.cisco.tiedie.dto.scim;

import com.cisco.tiedie.utils.ObjectMapperSingleton;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.SerializationFeature;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import java.util.Arrays;
import java.util.List;

import static org.junit.jupiter.api.Assertions.assertEquals;

class DeviceTest {
        final ObjectMapper mapper = ObjectMapperSingleton.getInstance();

        @BeforeEach
        void setup() {
                mapper.enable(SerializationFeature.INDENT_OUTPUT);
        }

        @Test
        @DisplayName("Device creation using builder")
        void testDeviceCreationUsingBuilder() throws JsonProcessingException {
                var device = Device.builder()
                                .deviceDisplayName("BLE Monitor")
                                .adminState(false)
                                .bleExtension(BleExtension.builder()
                                                .deviceMacAddress("AA:BB:CC:11:22:33")
                                                .isRandom(false)
                                                .versionSupport(Arrays.asList("4.1", "4.2", "5.0", "5.1", "5.2", "5.3"))
                                                .pairingPassKey(new BleExtension.PairingPassKey(123456))
                                                .build())
                                .build();

                String json = mapper.writeValueAsString(device);

                String expected = "{\n" +
                                "  \"schemas\" : [ \"urn:ietf:params:scim:schemas:core:2.0:Device\", \"urn:ietf:params:scim:schemas:extension:ble:2.0:Device\" ],\n"
                                +
                                "  \"deviceDisplayName\" : \"BLE Monitor\",\n" +
                                "  \"adminState\" : false,\n" +
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
                                "}";
                assertEquals(expected, json);

                device = Device.builder()
                                .deviceDisplayName("Zigbee Monitor")
                                .adminState(false)
                                .zigbeeExtension(ZigbeeExtension.builder()
                                                .versionSupport(List.of("3.0"))
                                                .deviceEui64Address("50325FFFFEE76728")
                                                .build())
                                .build();

                json = mapper.writeValueAsString(device);

                expected = "{\n" +
                                "  \"schemas\" : [ \"urn:ietf:params:scim:schemas:core:2.0:Device\", \"urn:ietf:params:scim:schemas:extension:zigbee:2.0:Device\" ],\n"
                                +
                                "  \"deviceDisplayName\" : \"Zigbee Monitor\",\n" +
                                "  \"adminState\" : false,\n" +
                                "  \"urn:ietf:params:scim:schemas:extension:zigbee:2.0:Device\" : {\n" +
                                "    \"versionSupport\" : [ \"3.0\" ],\n" +
                                "    \"deviceEui64Address\" : \"50325FFFFEE76728\"\n" +
                                "  }\n" +
                                "}";
                assertEquals(expected, json);

                device = Device.builder()
                                .deviceDisplayName("DPP Monitor")
                                .adminState(false)
                                .dppExtension(DppExtension.builder()
                                                .dppVersion(2)
                                                .bootstrappingMethod(List.of("QR"))
                                                .bootstrapKey("MDkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDIgADURzxmttZoIRIPWGoQMV00XHWCAQIhXruVWOz0NjlkIA=")
                                                .deviceMacAddress("AA:BB:CC:11:22:33")
                                                .classChannel(Arrays.asList("81/1", "115/36"))
                                                .serialNumber("4774LH2b4044")
                                                .build())
                                .build();

                json = mapper.writeValueAsString(device);

                expected = "{\n" +
                                "  \"schemas\" : [ \"urn:ietf:params:scim:schemas:core:2.0:Device\", \"urn:ietf:params:scim:schemas:extension:dpp:2.0:Device\" ],\n"
                                +
                                "  \"deviceDisplayName\" : \"DPP Monitor\",\n" +
                                "  \"adminState\" : false,\n" +
                                "  \"urn:ietf:params:scim:schemas:extension:dpp:2.0:Device\" : {\n" +
                                "    \"dppVersion\" : 2,\n" +
                                "    \"bootstrappingMethod\" : [ \"QR\" ],\n" +
                                "    \"bootstrapKey\" : \"MDkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDIgADURzxmttZoIRIPWGoQMV00XHWCAQIhXruVWOz0NjlkIA=\",\n"
                                +
                                "    \"deviceMacAddress\" : \"AA:BB:CC:11:22:33\",\n" +
                                "    \"classChannel\" : [ \"81/1\", \"115/36\" ],\n" +
                                "    \"serialNumber\" : \"4774LH2b4044\"\n" +
                                "  }\n" +
                                "}";
                assertEquals(expected, json);
        }

        @Test
        @DisplayName("Device creation")
        void testDeviceCreation() throws JsonProcessingException {
                var device = new Device();
                device.setDeviceDisplayName("BLE Monitor");
                device.setAdminState(false);
                var bleExtension = new BleExtension();
                bleExtension.setDeviceMacAddress("AA:BB:CC:11:22:33");
                bleExtension.setRandom(false);
                bleExtension.setVersionSupport(Arrays.asList("4.1", "4.2", "5.0", "5.1", "5.2", "5.3"));
                bleExtension.setPairingPassKey(new BleExtension.PairingPassKey(123456));
                device.setBleExtension(bleExtension);

                String json = mapper.writeValueAsString(device);

                String expected = "{\n" +
                                "  \"schemas\" : [ \"urn:ietf:params:scim:schemas:core:2.0:Device\", \"urn:ietf:params:scim:schemas:extension:ble:2.0:Device\" ],\n"
                                +
                                "  \"deviceDisplayName\" : \"BLE Monitor\",\n" +
                                "  \"adminState\" : false,\n" +
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
                                "}";
                assertEquals(expected, json);

                device.setBleExtension(null);
                device.setDeviceDisplayName("Zigbee Monitor");
                var zigbeeExtension = new ZigbeeExtension();
                zigbeeExtension.setVersionSupport(List.of("3.0"));
                zigbeeExtension.setDeviceEui64Address("50325FFFFEE76728");
                device.setZigbeeExtension(zigbeeExtension);

                json = mapper.writeValueAsString(device);

                expected = "{\n" +
                                "  \"schemas\" : [ \"urn:ietf:params:scim:schemas:core:2.0:Device\", \"urn:ietf:params:scim:schemas:extension:zigbee:2.0:Device\" ],\n"
                                +
                                "  \"deviceDisplayName\" : \"Zigbee Monitor\",\n" +
                                "  \"adminState\" : false,\n" +
                                "  \"urn:ietf:params:scim:schemas:extension:zigbee:2.0:Device\" : {\n" +
                                "    \"versionSupport\" : [ \"3.0\" ],\n" +
                                "    \"deviceEui64Address\" : \"50325FFFFEE76728\"\n" +
                                "  }\n" +
                                "}";
                assertEquals(expected, json);

                device.setZigbeeExtension(null);
                device.setDeviceDisplayName("DPP Monitor");
                var dppExtension = new DppExtension();
                dppExtension.setDppVersion(2);
                dppExtension.setBootstrappingMethod(List.of("QR"));
                dppExtension.setBootstrapKey(
                                "MDkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDIgADURzxmttZoIRIPWGoQMV00XHWCAQIhXruVWOz0NjlkIA=");
                dppExtension.setDeviceMacAddress("AA:BB:CC:11:22:33");
                dppExtension.setClassChannel(Arrays.asList("81/1", "115/36"));
                dppExtension.setSerialNumber("4774LH2b4044");
                device.setDppExtension(dppExtension);
                json = mapper.writeValueAsString(device);

                expected = "{\n" +
                                "  \"schemas\" : [ \"urn:ietf:params:scim:schemas:core:2.0:Device\", \"urn:ietf:params:scim:schemas:extension:dpp:2.0:Device\" ],\n"
                                +
                                "  \"deviceDisplayName\" : \"DPP Monitor\",\n" +
                                "  \"adminState\" : false,\n" +
                                "  \"urn:ietf:params:scim:schemas:extension:dpp:2.0:Device\" : {\n" +
                                "    \"dppVersion\" : 2,\n" +
                                "    \"bootstrappingMethod\" : [ \"QR\" ],\n" +
                                "    \"bootstrapKey\" : \"MDkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDIgADURzxmttZoIRIPWGoQMV00XHWCAQIhXruVWOz0NjlkIA=\",\n"
                                +
                                "    \"deviceMacAddress\" : \"AA:BB:CC:11:22:33\",\n" +
                                "    \"classChannel\" : [ \"81/1\", \"115/36\" ],\n" +
                                "    \"serialNumber\" : \"4774LH2b4044\"\n" +
                                "  }\n" +
                                "}";
                assertEquals(expected, json);
        }

        @Test
        @DisplayName("Test device parsing")
        void testDeviceParsing() throws JsonProcessingException {
                String json = "{\n" +
                                "  \"schemas\" : [ \"urn:ietf:params:scim:schemas:core:2.0:Device\", \"urn:ietf:params:scim:schemas:extension:ble:2.0:Device\" ],\n"
                                +
                                "  \"deviceDisplayName\" : \"BLE Monitor\",\n" +
                                "  \"adminState\" : false,\n" +
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
                                "}";

                var device = mapper.readValue(json, Device.class);

                var expected = Device.builder()
                                .deviceDisplayName("BLE Monitor")
                                .adminState(false)
                                .bleExtension(BleExtension.builder()
                                                .deviceMacAddress("AA:BB:CC:11:22:33")
                                                .isRandom(false)
                                                .versionSupport(Arrays.asList("4.1", "4.2", "5.0", "5.1", "5.2", "5.3"))
                                                .pairingPassKey(new BleExtension.PairingPassKey(123456))
                                                .build())
                                .build();

                assertEquals(expected, device);

                json = "{\n" +
                                "  \"schemas\" : [ \"urn:ietf:params:scim:schemas:core:2.0:Device\", \"urn:ietf:params:scim:schemas:extension:zigbee:2.0:Device\" ],\n"
                                +
                                "  \"deviceDisplayName\" : \"Zigbee Monitor\",\n" +
                                "  \"adminState\" : false,\n" +
                                "  \"urn:ietf:params:scim:schemas:extension:zigbee:2.0:Device\" : {\n" +
                                "    \"versionSupport\" : [ \"3.0\" ],\n" +
                                "    \"deviceEui64Address\" : \"50325FFFFEE76728\"\n" +
                                "  }\n" +
                                "}";

                device = mapper.readValue(json, Device.class);

                expected = Device.builder()
                                .deviceDisplayName("Zigbee Monitor")
                                .adminState(false)
                                .zigbeeExtension(ZigbeeExtension.builder()
                                                .versionSupport(List.of("3.0"))
                                                .deviceEui64Address("50325FFFFEE76728")
                                                .build())
                                .build();

                assertEquals(expected, device);

                json = "{\n" +
                                "  \"schemas\" : [ \"urn:ietf:params:scim:schemas:core:2.0:Device\", \"urn:ietf:params:scim:schemas:extension:dpp:2.0:Device\" ],\n"
                                +
                                "  \"deviceDisplayName\" : \"DPP Monitor\",\n" +
                                "  \"adminState\" : false,\n" +
                                "  \"urn:ietf:params:scim:schemas:extension:dpp:2.0:Device\" : {\n" +
                                "    \"dppVersion\" : 2,\n" +
                                "    \"bootstrappingMethod\" : [ \"QR\" ],\n" +
                                "    \"bootstrapKey\" : \"MDkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDIgADURzxmttZoIRIPWGoQMV00XHWCAQIhXruVWOz0NjlkIA=\",\n"
                                +
                                "    \"deviceMacAddress\" : \"AA:BB:CC:11:22:33\",\n" +
                                "    \"classChannel\" : [ \"81/1\", \"115/36\" ],\n" +
                                "    \"serialNumber\" : \"4774LH2b4044\"\n" +
                                "  }\n" +
                                "}";

                device = mapper.readValue(json, Device.class);

                expected = Device.builder()
                                .deviceDisplayName("DPP Monitor")
                                .adminState(false)
                                .dppExtension(DppExtension.builder()
                                                .dppVersion(2)
                                                .bootstrappingMethod(List.of("QR"))
                                                .bootstrapKey("MDkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDIgADURzxmttZoIRIPWGoQMV00XHWCAQIhXruVWOz0NjlkIA=")
                                                .deviceMacAddress("AA:BB:CC:11:22:33")
                                                .classChannel(Arrays.asList("81/1", "115/36"))
                                                .serialNumber("4774LH2b4044")
                                                .build())
                                .build();

                assertEquals(expected, device);
        }

    @Test
    @DisplayName("Test endpoint extension")
    void testEndpointExtension() throws JsonProcessingException {
        var device = Device.builder()
                .deviceDisplayName("BLE Monitor")
                .adminState(false)
                .bleExtension(BleExtension.builder()
                        .deviceMacAddress("AA:BB:CC:11:22:33")
                        .isRandom(false)
                        .versionSupport(Arrays.asList("4.1", "4.2", "5.0", "5.1", "5.2", "5.3"))
                        .pairingPassKey(new BleExtension.PairingPassKey(123456))
                        .build())
                .endpointAppsExtension(
                        new EndpointAppsExtension.Builder()
                                .onboardingUrl("onboarding-app")
                                .deviceControlUrl(List.of("control-app"))
                                .dataReceiverUrl(List.of("data-app"))
                                .build()                
                )
                .build();

        var json = mapper.writeValueAsString(device);
        var expected = "{\n" +
                "  \"schemas\" : [ \"urn:ietf:params:scim:schemas:core:2.0:Device\", \"urn:ietf:params:scim:schemas:extension:ble:2.0:Device\", \"urn:ietf:params:scim:schemas:extension:endpointApps:2.0:Device\" ],\n" +
                "  \"deviceDisplayName\" : \"BLE Monitor\",\n" +
                "  \"adminState\" : false,\n" +
                "  \"urn:ietf:params:scim:schemas:extension:ble:2.0:Device\" : {\n" +
                "    \"pairingMethods\" : [ \"urn:ietf:params:scim:schemas:extension:pairingPassKey:2.0:Device\" ],\n" +
                "    \"versionSupport\" : [ \"4.1\", \"4.2\", \"5.0\", \"5.1\", \"5.2\", \"5.3\" ],\n" +
                "    \"deviceMacAddress\" : \"AA:BB:CC:11:22:33\",\n" +
                "    \"isRandom\" : false,\n" +
                "    \"urn:ietf:params:scim:schemas:extension:pairingPassKey:2.0:Device\" : {\n" +
                "      \"key\" : 123456\n" +
                "    }\n" +
                "  },\n" +
                "  \"urn:ietf:params:scim:schemas:extension:endpointAppsExt:2.0:Device\" : {\n" +
                "    \"onboardingUrl\" : \"onboarding-app\",\n" +
                "    \"deviceControlUrl\" : [ \"control-app\" ],\n" +
                "    \"dataReceiverUrl\" : [ \"data-app\" ]\n" +
                "  }\n" +
                "}";

        assertEquals(expected, json);
    }
}
