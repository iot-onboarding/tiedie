// Copyright (c) 2023, Cisco Systems, Inc. and/or its affiliates.
// All rights reserved.
// See LICENSE file in this distribution.
// SPDX-License-Identifier: Apache-2.0

package com.example.tiediesampleapp.controller;

import com.cisco.tiedie.clients.ControlClient;
import com.cisco.tiedie.clients.OnboardingClient;
import com.cisco.tiedie.dto.HttpResponse;
import com.cisco.tiedie.dto.control.DataParameter;
import com.cisco.tiedie.dto.scim.BleExtension;
import com.cisco.tiedie.dto.nipc.DataAppRegistration;
import com.cisco.tiedie.dto.nipc.Event;
import com.cisco.tiedie.dto.nipc.NipcHttp;
import com.cisco.tiedie.dto.nipc.NipcProblemType;
import com.cisco.tiedie.dto.nipc.NipcResponse;
import com.cisco.tiedie.dto.nipc.PropertyReadResult;
import com.cisco.tiedie.dto.nipc.PropertyWriteResult;
import com.cisco.tiedie.dto.nipc.ProblemDetails;
import com.cisco.tiedie.dto.nipc.SdfModel;
import com.cisco.tiedie.dto.scim.Device;
import com.cisco.tiedie.dto.scim.DeviceListResponse;
import com.cisco.tiedie.dto.scim.EndpointApp;
import com.cisco.tiedie.dto.scim.EndpointAppType;
import com.example.tiediesampleapp.service.OAuthService;
import com.example.tiediesampleapp.service.TiedieClientManager;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.mockito.ArgumentCaptor;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.http.MediaType;
import org.springframework.mock.web.MockMultipartFile;
import org.springframework.test.web.servlet.MockMvc;

import java.net.URI;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.Map;

import static org.hamcrest.Matchers.containsString;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.multipart;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.content;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.redirectedUrl;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@SpringBootTest
@AutoConfigureMockMvc
class DeviceControllerTest {
    @Autowired
    private MockMvc mockMvc;

    @MockBean
    private TiedieClientManager tiedieClientManager;

    @MockBean
    private OAuthService oAuthService;

    private OnboardingClient onboardingClient;
    private ControlClient controlClient;

    @BeforeEach
    void setUp() throws Exception {
        onboardingClient = mock(OnboardingClient.class);
        controlClient = mock(ControlClient.class);

        when(tiedieClientManager.isOauthEnabled()).thenReturn(false);
        when(tiedieClientManager.getOnboardingClient()).thenReturn(onboardingClient);
        when(tiedieClientManager.getControlClient()).thenReturn(controlClient);
    }

    @Test
    void rootRedirectsToDevices() throws Exception {
        mockMvc.perform(get("/"))
                .andExpect(status().is3xxRedirection())
                .andExpect(redirectedUrl("/devices"));
    }

    @Test
    void devicesPageRendersDevices() throws Exception {
        Device device = Device.builder()
                .id("device-1")
                .displayName("Device One")
                .active(false)
                .build();

        DeviceListResponse listResponse = new DeviceListResponse();
        listResponse.setResources(List.of(device));

        when(onboardingClient.getDevices()).thenReturn(httpResponse(200, "OK", listResponse));

        mockMvc.perform(get("/devices"))
                .andExpect(status().isOk())
                .andExpect(content().string(containsString("device-1")))
                .andExpect(content().string(containsString("Device One")));
    }

    @Test
    void dataAppRedirectsToSubscriptionTopic() throws Exception {
        EndpointApp dataEndpoint = EndpointApp.builder()
                .id("data-app-id")
                .applicationName("data-app")
                .applicationType(EndpointAppType.TELEMETRY)
                .build();
        when(tiedieClientManager.getDataEndpointApp()).thenReturn(dataEndpoint);

        mockMvc.perform(get("/data_app"))
                .andExpect(status().is3xxRedirection())
                .andExpect(redirectedUrl("/subscription?event=data-app%2Fdata-app-id%2F%23"));
    }

    @Test
    void subscriptionPageRendersSelectedEvent() throws Exception {
        mockMvc.perform(get("/subscription")
                        .param("event", "data-app/data-app-id/#"))
                .andExpect(status().isOk())
                .andExpect(content().string(containsString("data-app/data-app-id/#")));
    }

    @Test
    void devicePageRendersWithNoConnectionData() throws Exception {
        Device device = Device.builder()
                .id("device-1")
                .displayName("Device One")
                .active(false)
                .bleExtension(BleExtension.builder()
                        .deviceMacAddress("AA:BB:CC:11:22:33")
                        .isRandom(false)
                        .versionSupport(List.of("5.0"))
                        .build())
                .build();

        when(onboardingClient.getDevice("device-1")).thenReturn(httpResponse(200, "OK", device));
        when(controlClient.getSdfModels()).thenReturn(new NipcResponse<>(new NipcHttp(200, "OK", Map.of()), List.of(), null));
        when(controlClient.getConnection(device)).thenReturn(new NipcResponse<>(new NipcHttp(200, "OK", Map.of()), null, null));
        when(controlClient.getAllEvents("device-1")).thenReturn(new NipcResponse<>(new NipcHttp(200, "OK", Map.of()), List.of(), null));

        mockMvc.perform(get("/devices/device-1"))
                .andExpect(status().isOk())
                .andExpect(content().string(containsString("Device Information")))
                .andExpect(content().string(containsString("device-1")));
    }

    @Test
    void updateDevicePageRendersDevice() throws Exception {
        Device device = Device.builder()
                .id("device-1")
                .displayName("Device One")
                .active(true)
                .bleExtension(BleExtension.builder()
                        .deviceMacAddress("AA:BB:CC:11:22:33")
                        .versionSupport(List.of("5.0"))
                        .isRandom(true)
                        .mobility(true)
                        .build())
                .build();
        when(onboardingClient.getDevice("device-1")).thenReturn(httpResponse(200, "OK", device));

        mockMvc.perform(get("/devices/device-1/update"))
                .andExpect(status().isOk())
                .andExpect(content().string(containsString("Update Device")))
                .andExpect(content().string(containsString("Device One")));
    }

    @Test
    void updateDeviceUpdatesAndRedirects() throws Exception {
        when(tiedieClientManager.getDeviceEndpointApps()).thenReturn(List.of());
        when(onboardingClient.updateDevice(any(Device.class)))
                .thenReturn(httpResponse(200, "OK", Device.builder().id("device-1").build()));

        mockMvc.perform(post("/devices/device-1/update")
                        .param("displayName", "Updated Device")
                        .param("active", "true")
                        .param("deviceMacAddress", "AA:BB:CC:11:22:33")
                        .param("versionSupport", "5.0", "5.1")
                        .param("isRandom", "true")
                        .param("mobility", "true")
                        .param("pairingMethod", "passKey")
                        .param("passKey", "123456"))
                .andExpect(status().is3xxRedirection())
                .andExpect(redirectedUrl("/devices/device-1"));

        ArgumentCaptor<Device> deviceCaptor = ArgumentCaptor.forClass(Device.class);
        verify(onboardingClient).updateDevice(deviceCaptor.capture());
        assertEquals("device-1", deviceCaptor.getValue().getId());
        assertEquals(true, deviceCaptor.getValue().getBleExtension().getMobility());
    }

    @Test
    void connectParsesServiceUuids() throws Exception {
        Device device = Device.builder().id("device-1").displayName("Device One").active(false).build();
        when(onboardingClient.getDevice("device-1")).thenReturn(httpResponse(200, "OK", device));
        when(controlClient.connect(eq(device), any())).thenReturn(new NipcResponse<>(new NipcHttp(200, "OK", Map.of()), List.<DataParameter>of(), null));

        mockMvc.perform(post("/devices/device-1/connect")
                        .param("serviceUUIDs", "1800, 180A"))
                .andExpect(status().is3xxRedirection())
                .andExpect(redirectedUrl("/devices/device-1"));

        ArgumentCaptor<com.cisco.tiedie.dto.control.ble.BleConnectRequest> requestCaptor =
                ArgumentCaptor.forClass(com.cisco.tiedie.dto.control.ble.BleConnectRequest.class);
        verify(controlClient).connect(eq(device), requestCaptor.capture());
        assertEquals(2, requestCaptor.getValue().getServices().size());
        assertEquals("1800", requestCaptor.getValue().getServices().get(0).getServiceID());
        assertEquals("180A", requestCaptor.getValue().getServices().get(1).getServiceID());
    }

    @Test
    void enableEventCreatesDataAppWhenMissing() throws Exception {
        EndpointApp dataEndpoint = EndpointApp.builder()
                .id("data-app-id")
                .applicationName("data-app")
                .applicationType(EndpointAppType.TELEMETRY)
                .build();
        when(tiedieClientManager.getDataEndpointApp()).thenReturn(dataEndpoint);
        when(tiedieClientManager.getDataAppMqttType()).thenReturn("client");

        NipcResponse<DataAppRegistration> missingDataApp = new NipcResponse<>(
                new NipcHttp(404, "Not Found", Map.of()),
                null,
                new ProblemDetails(NipcProblemType.ABOUT_BLANK, 404, "Not Found", "missing")
        );
        when(controlClient.getDataApp("data-app-id")).thenReturn(missingDataApp);
        when(controlClient.createDataApp(eq("data-app-id"), any()))
                .thenReturn(new NipcResponse<>(new NipcHttp(200, "OK", Map.of()), new DataAppRegistration(), null));
        when(controlClient.enableEvent("device-1", "event-1"))
                .thenReturn(new NipcResponse<>(new NipcHttp(200, "OK", Map.of()), "instance-1", null));

        mockMvc.perform(post("/devices/device-1/event")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"sdfName\":\"event-1\",\"enable\":true}"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.success").value(true))
                .andExpect(jsonPath("$.instanceId").value("instance-1"));

        verify(controlClient).createDataApp(eq("data-app-id"), any(DataAppRegistration.class));
        verify(controlClient).enableEvent("device-1", "event-1");
    }

    @Test
    void disableEventDeletesDataAppWhenLastEventRemoved() throws Exception {
        EndpointApp dataEndpoint = EndpointApp.builder()
                .id("data-app-id")
                .applicationName("data-app")
                .applicationType(EndpointAppType.TELEMETRY)
                .build();
        when(tiedieClientManager.getDataEndpointApp()).thenReturn(dataEndpoint);

        Event event = new Event();
        event.setEvent("event-1");
        DataAppRegistration registration = new DataAppRegistration();
        registration.setEvents(List.of(event));
        registration.setMqttClient(true);

        when(controlClient.disableEvent("device-1", "instance-1"))
                .thenReturn(nipcResponse(null));
        when(controlClient.getDataApp("data-app-id"))
                .thenReturn(nipcResponse(registration));
        when(controlClient.deleteDataApp("data-app-id"))
                .thenReturn(nipcResponse(null));

        mockMvc.perform(post("/devices/device-1/event")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"sdfName\":\"event-1\",\"enable\":false,\"instanceId\":\"instance-1\"}"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.success").value(true));

        verify(controlClient).disableEvent("device-1", "instance-1");
        verify(controlClient).deleteDataApp("data-app-id");
    }

    @Test
    void readPropertyReturnsResults() throws Exception {
        PropertyReadResult readResult = new PropertyReadResult();
        readResult.setProperty("temperature");
        readResult.setValue("22");
        when(controlClient.readProperty("device-1", "urn:example#/Thing/temp"))
                .thenReturn(nipcResponse(List.of(readResult)));

        mockMvc.perform(post("/devices/device-1/read")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"sdfName\":\"urn:example#/Thing/temp\"}"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$[0].property").value("temperature"))
                .andExpect(jsonPath("$[0].value").value("22"));
    }

    @Test
    void writePropertyReturnsResults() throws Exception {
        PropertyWriteResult writeResult = new PropertyWriteResult();
        writeResult.setStatus(200);
        writeResult.setTitle("OK");
        writeResult.setDetail("written");
        when(controlClient.writeProperty("device-1", "urn:example#/Thing/temp", "24"))
                .thenReturn(nipcResponse(List.of(writeResult)));

        mockMvc.perform(post("/devices/device-1/write")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"sdfName\":\"urn:example#/Thing/temp\",\"value\":\"24\"}"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$[0].status").value(200))
                .andExpect(jsonPath("$[0].detail").value("written"));
    }

    @Test
    void registerSdfModelRedirectsToDevicePage() throws Exception {
        when(controlClient.getSdfModels()).thenReturn(nipcResponse(List.of()));
        when(controlClient.registerSdfModel(any(SdfModel.class))).thenReturn(nipcResponse(List.of()));

        String sdfJson = """
                {
                  "namespace": { "default": "urn:example:device" },
                  "defaultNamespace": "default",
                  "sdfThing": { "Thing": {} }
                }
                """;
        MockMultipartFile file = new MockMultipartFile(
                "sdfFile",
                "thing.sdf.json",
                MediaType.APPLICATION_JSON_VALUE,
                sdfJson.getBytes(StandardCharsets.UTF_8)
        );

        mockMvc.perform(multipart("/devices/device-1/sdf").file(file))
                .andExpect(status().is3xxRedirection())
                .andExpect(redirectedUrl("/devices/device-1"));
    }

    @Test
    void deleteSdfModelDecodesPathAndRedirects() throws Exception {
        when(controlClient.unregisterSdfModel("urn:example#Thing"))
                .thenReturn(nipcResponse(null));

        URI uri = URI.create("/devices/device-1/deleteSdf/urn:example%23Thing");
        mockMvc.perform(post(uri))
                .andExpect(status().is3xxRedirection())
                .andExpect(redirectedUrl("/devices/device-1"));

        verify(controlClient).unregisterSdfModel("urn:example#Thing");
    }

    @Test
    void oauthGateRedirectsWhenTokenMissing() throws Exception {
        when(tiedieClientManager.isOauthEnabled()).thenReturn(true);
        when(tiedieClientManager.hasOauthToken()).thenReturn(false);

        mockMvc.perform(get("/devices"))
                .andExpect(status().is3xxRedirection())
                .andExpect(redirectedUrl("/oauth2/authorize"));
    }

    private static <T> HttpResponse<T> httpResponse(int status, String message, T body) {
        HttpResponse<T> response = new HttpResponse<>();
        response.setStatusCode(status);
        response.setMessage(message);
        response.setBody(body);
        return response;
    }

    private static <T> NipcResponse<T> nipcResponse(T body) {
        return new NipcResponse<>(new NipcHttp(200, "OK", Map.of()), body, null);
    }
}
