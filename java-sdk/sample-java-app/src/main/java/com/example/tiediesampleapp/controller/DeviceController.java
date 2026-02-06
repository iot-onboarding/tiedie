// Copyright (c) 2023, Cisco Systems, Inc. and/or its affiliates.
// All rights reserved.
// See LICENSE file in this distribution.
// SPDX-License-Identifier: Apache-2.0

package com.example.tiediesampleapp.controller;

import com.cisco.tiedie.clients.ControlClient;
import com.cisco.tiedie.clients.OnboardingClient;
import com.cisco.tiedie.dto.HttpResponse;
import com.cisco.tiedie.dto.control.DataParameter;
import com.cisco.tiedie.dto.control.DataResponse;
import com.cisco.tiedie.dto.control.ble.BleConnectRequest;
import com.cisco.tiedie.dto.control.ble.BleDataParameter;
import com.cisco.tiedie.dto.control.ble.BleService;
import com.cisco.tiedie.dto.nipc.DataAppRegistration;
import com.cisco.tiedie.dto.nipc.Event;
import com.cisco.tiedie.dto.nipc.ModelRegistrationResponse;
import com.cisco.tiedie.dto.nipc.MqttBrokerConfig;
import com.cisco.tiedie.dto.nipc.NipcResponse;
import com.cisco.tiedie.dto.nipc.PropertyReadResult;
import com.cisco.tiedie.dto.nipc.PropertyWriteResult;
import com.cisco.tiedie.dto.nipc.SdfModel;
import com.cisco.tiedie.dto.nipc.TiedieEventResponse;
import com.cisco.tiedie.dto.scim.BleExtension;
import com.cisco.tiedie.dto.scim.Device;
import com.cisco.tiedie.dto.scim.DeviceListResponse;
import com.cisco.tiedie.dto.scim.EndpointAppsExtension;
import com.example.tiediesampleapp.service.TiedieClientManager;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.ResponseBody;
import org.springframework.web.multipart.MultipartFile;
import org.springframework.web.util.UriUtils;

import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Base64;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.stream.Collectors;

@Controller
public class DeviceController {
    private final TiedieClientManager tiedieClientManager;
    private final ObjectMapper objectMapper = new ObjectMapper();

    public DeviceController(TiedieClientManager tiedieClientManager) {
        this.tiedieClientManager = tiedieClientManager;
    }

    @GetMapping("/")
    public String index() {
        return "redirect:/devices";
    }

    @GetMapping("/devices")
    public String getAllDevices(Model model) throws Exception {
        HttpResponse<DeviceListResponse> response = onboardingClient().getDevices();
        List<Device> devices = response.getBody() == null || response.getBody().getResources() == null
                ? List.of()
                : response.getBody().getResources();

        model.addAttribute("devices", devices);
        return "devices";
    }

    @GetMapping("/data_app")
    public String dataAppRedirect() throws Exception {
        var dataApp = tiedieClientManager.getDataEndpointApp();
        if (dataApp == null || dataApp.getId() == null) {
            return "redirect:/devices";
        }

        String event = "data-app/" + dataApp.getId() + "/#";
        return "redirect:/subscription?event=" + UriUtils.encode(event, StandardCharsets.UTF_8);
    }

    @GetMapping("/subscription")
    public String getSubscription(@RequestParam("event") String event, Model model) {
        model.addAttribute("event", event);
        return "subscription";
    }

    @GetMapping("/devices/add")
    public String addDevicePage() {
        return "device_add";
    }

    @PostMapping("/devices/add")
    public String addDevice(
            @RequestParam("displayName") String displayName,
            @RequestParam(name = "active", defaultValue = "false") boolean active,
            @RequestParam("deviceMacAddress") String deviceMacAddress,
            @RequestParam(name = "versionSupport", required = false) List<String> versionSupport,
            @RequestParam(name = "isRandom", defaultValue = "false") boolean isRandom,
            @RequestParam(name = "mobility", defaultValue = "false") boolean mobility,
            @RequestParam(name = "pairingMethod", defaultValue = "null") String pairingMethod,
            @RequestParam(name = "passKey", required = false) String passKey,
            Model model
    ) throws Exception {
        Device device = buildDeviceFromForm(
                null,
                displayName,
                active,
                deviceMacAddress,
                versionSupport,
                isRandom,
                mobility,
                pairingMethod,
                passKey
        );

        HttpResponse<Device> response = onboardingClient().createDevice(device);
        if (response.getStatusCode() != 201 || response.getBody() == null) {
            return error(model, "Failed to create device");
        }

        return "redirect:/devices";
    }

    @GetMapping("/devices/{id}/update")
    public String updateDevicePage(@PathVariable("id") String id, Model model) throws Exception {
        HttpResponse<Device> response = onboardingClient().getDevice(id);
        if (response.getStatusCode() != 200 || response.getBody() == null) {
            return error(model, "Failed to get device");
        }

        model.addAttribute("device", response.getBody());
        return "device_update";
    }

    @PostMapping("/devices/{id}/update")
    public String updateDevice(
            @PathVariable("id") String id,
            @RequestParam("displayName") String displayName,
            @RequestParam(name = "active", defaultValue = "false") boolean active,
            @RequestParam("deviceMacAddress") String deviceMacAddress,
            @RequestParam(name = "versionSupport", required = false) List<String> versionSupport,
            @RequestParam(name = "isRandom", defaultValue = "false") boolean isRandom,
            @RequestParam(name = "mobility", defaultValue = "false") boolean mobility,
            @RequestParam(name = "pairingMethod", defaultValue = "null") String pairingMethod,
            @RequestParam(name = "passKey", required = false) String passKey,
            Model model
    ) throws Exception {
        Device device = buildDeviceFromForm(
                id,
                displayName,
                active,
                deviceMacAddress,
                versionSupport,
                isRandom,
                mobility,
                pairingMethod,
                passKey
        );

        HttpResponse<Device> response = onboardingClient().updateDevice(device);
        if ((response.getStatusCode() != 200 && response.getStatusCode() != 201) || response.getBody() == null) {
            return error(model, "Failed to update device");
        }

        return "redirect:/devices/{id}";
    }

    @GetMapping("/devices/{id}")
    public String getDevice(@PathVariable("id") String id, Model model) throws Exception {
        HttpResponse<Device> response = onboardingClient().getDevice(id);
        if (response.getStatusCode() != 200 || response.getBody() == null) {
            return error(model, "Failed to get device");
        }

        Device device = response.getBody();

        Map<String, SdfModel> sdfModels = new LinkedHashMap<>();
        NipcResponse<List<ModelRegistrationResponse>> sdfNamesResponse = controlClient().getSdfModels();
        if (sdfNamesResponse.isSuccess() && sdfNamesResponse.getBody() != null) {
            for (ModelRegistrationResponse sdfNameResponse : sdfNamesResponse.getBody()) {
                if (sdfNameResponse == null || sdfNameResponse.getSdfName() == null) {
                    continue;
                }
                NipcResponse<SdfModel> sdfResponse = controlClient().getSdfModel(sdfNameResponse.getSdfName());
                if (sdfResponse.isSuccess() && sdfResponse.getBody() != null) {
                    sdfModels.put(sdfNameResponse.getSdfName(), sdfResponse.getBody());
                }
            }
        }

        NipcResponse<List<DataParameter>> dataResponse = controlClient().getConnection(device);
        List<BleDataParameter> parameters = null;
        if (dataResponse.isSuccess() && dataResponse.getBody() != null) {
            parameters = dataResponse.getBody().stream()
                    .filter(BleDataParameter.class::isInstance)
                    .map(BleDataParameter.class::cast)
                    .collect(Collectors.toList());
        }

        List<TiedieEventResponse> events = List.of();
        Map<String, String> enabledEvents = new LinkedHashMap<>();
        NipcResponse<List<TiedieEventResponse>> eventsResponse = controlClient().getAllEvents(id);
        if (eventsResponse.isSuccess() && eventsResponse.getBody() != null) {
            events = eventsResponse.getBody();
            for (TiedieEventResponse eventResponse : events) {
                if (eventResponse == null || eventResponse.getEvent() == null) {
                    continue;
                }
                enabledEvents.put(eventResponse.getEvent(), eventResponse.getInstanceId());
            }
        }

        model.addAttribute("device", device);
        model.addAttribute("parameters", parameters);
        model.addAttribute("sdfModels", sdfModels);
        model.addAttribute("events", events);
        model.addAttribute("enabledEvents", enabledEvents);
        return "device";
    }

    @PostMapping("/devices/{id}/connect")
    public String connectDevice(
            @PathVariable("id") String id,
            @RequestParam(name = "serviceUUIDs", required = false) String serviceUUIDs,
            Model model
    ) throws Exception {
        HttpResponse<Device> response = onboardingClient().getDevice(id);
        if (response.getStatusCode() != 200 || response.getBody() == null) {
            return error(model, "Failed to get device");
        }

        List<BleService> services = parseServiceUUIDs(serviceUUIDs);
        BleConnectRequest connectRequest = BleConnectRequest.builder().services(services).build();
        NipcResponse<List<DataParameter>> connectResponse = controlClient().connect(response.getBody(), connectRequest);
        if (!connectResponse.isSuccess()) {
            return error(model, getErrorMessage(connectResponse));
        }

        return "redirect:/devices/{id}";
    }

    @PostMapping("/devices/{id}/disconnect")
    public String disconnectDevice(@PathVariable("id") String id, Model model) throws Exception {
        HttpResponse<Device> response = onboardingClient().getDevice(id);
        if (response.getStatusCode() != 200 || response.getBody() == null) {
            return error(model, "Failed to get device");
        }

        NipcResponse<?> disconnectResponse = controlClient().disconnect(response.getBody());
        if (!disconnectResponse.isSuccess()) {
            return error(model, getErrorMessage(disconnectResponse));
        }

        return "redirect:/devices/{id}";
    }

    @PostMapping("/devices/{id}/delete")
    public String deleteDevice(@PathVariable("id") String id, Model model) throws Exception {
        HttpResponse<Void> response = onboardingClient().deleteDevice(id);
        if (response.getStatusCode() != 204) {
            return error(model, "Failed to delete device");
        }

        return "redirect:/devices";
    }

    @PostMapping(value = "/devices/{id}/svc/{svcUUID}/char/{charUUID}/read", produces = "application/json")
    @ResponseBody
    public DataResponse readCharacteristic(
            @PathVariable("id") String id,
            @PathVariable("svcUUID") String svcUUID,
            @PathVariable("charUUID") String charUUID
    ) throws Exception {
        Device device = new Device();
        device.setId(id);

        NipcResponse<DataResponse> response = controlClient().read(device, svcUUID, charUUID);
        return response.getBody() == null ? new DataResponse() : response.getBody();
    }

    @PostMapping(
            value = "/devices/{id}/svc/{svcUUID}/char/{charUUID}/write",
            consumes = "application/json",
            produces = "application/json"
    )
    @ResponseBody
    public DataResponse writeCharacteristic(
            @PathVariable("id") String id,
            @PathVariable("svcUUID") String svcUUID,
            @PathVariable("charUUID") String charUUID,
            @RequestBody Map<String, Object> payload
    ) throws Exception {
        String value = payload.get("value") == null ? "" : payload.get("value").toString();
        Device device = new Device();
        device.setId(id);

        NipcResponse<DataResponse> response = controlClient().write(device, svcUUID, charUUID, value);
        return response.getBody() == null ? new DataResponse() : response.getBody();
    }

    @PostMapping(value = "/devices/{id}/read", consumes = "application/json", produces = "application/json")
    @ResponseBody
    public List<PropertyReadResult> readProperty(
            @PathVariable("id") String id,
            @RequestBody Map<String, Object> payload
    ) throws Exception {
        String sdfName = payload.get("sdfName") == null ? null : payload.get("sdfName").toString();
        if (sdfName == null || sdfName.isBlank()) {
            return List.of();
        }

        NipcResponse<List<PropertyReadResult>> response = controlClient().readProperty(id, sdfName);
        return response.getBody() == null ? List.of() : response.getBody();
    }

    @PostMapping(value = "/devices/{id}/write", consumes = "application/json", produces = "application/json")
    @ResponseBody
    public List<PropertyWriteResult> writeProperty(
            @PathVariable("id") String id,
            @RequestBody Map<String, Object> payload
    ) throws Exception {
        String sdfName = payload.get("sdfName") == null ? null : payload.get("sdfName").toString();
        String value = payload.get("value") == null ? null : payload.get("value").toString();
        if (sdfName == null || value == null || sdfName.isBlank() || value.isBlank()) {
            return List.of();
        }

        NipcResponse<List<PropertyWriteResult>> response = controlClient().writeProperty(id, sdfName, value);
        return response.getBody() == null ? List.of() : response.getBody();
    }

    @PostMapping("/devices/{id}/sdf")
    public String registerSdfModel(
            @PathVariable("id") String id,
            @RequestParam("sdfFile") MultipartFile sdfFile,
            Model model
    ) throws Exception {
        if (sdfFile.isEmpty()) {
            return error(model, "No SDF file uploaded");
        }

        SdfModel sdfModel = objectMapper.readValue(sdfFile.getBytes(), SdfModel.class);
        String sdfName = resolveSdfName(sdfModel);

        NipcResponse<List<ModelRegistrationResponse>> modelsResponse = controlClient().getSdfModels();
        boolean exists = modelsResponse.isSuccess()
                && modelsResponse.getBody() != null
                && modelsResponse.getBody().stream()
                .filter(Objects::nonNull)
                .anyMatch(item -> sdfName.equals(item.getSdfName()));

        NipcResponse<?> response = exists
                ? controlClient().updateSdfModel(sdfName, sdfModel)
                : controlClient().registerSdfModel(sdfModel);

        if (!response.isSuccess()) {
            return error(model, "Failed to register SDF model: " + getErrorMessage(response));
        }

        return "redirect:/devices/{id}";
    }

    @PostMapping("/devices/{id}/deleteSdf/{sdfName}")
    public String deleteSdfModel(
            @PathVariable("id") String id,
            @PathVariable("sdfName") String encodedSdfName,
            Model model
    ) throws Exception {
        String sdfName = java.net.URLDecoder.decode(encodedSdfName, StandardCharsets.UTF_8);
        NipcResponse<ModelRegistrationResponse> response = controlClient().unregisterSdfModel(sdfName);
        if (!response.isSuccess()) {
            return error(model, "Failed to delete SDF model: " + getErrorMessage(response));
        }

        return "redirect:/devices/{id}";
    }

    @PostMapping(value = "/devices/{id}/event", consumes = "application/json", produces = "application/json")
    @ResponseBody
    public ResponseEntity<Map<String, Object>> updateEvent(
            @PathVariable("id") String id,
            @RequestBody Map<String, Object> payload
    ) throws Exception {
        String sdfName = payload.get("sdfName") == null ? null : payload.get("sdfName").toString();
        boolean enable = payload.get("enable") != null && Boolean.parseBoolean(payload.get("enable").toString());
        String instanceId = payload.get("instanceId") == null ? null : payload.get("instanceId").toString();

        if (sdfName == null || sdfName.isBlank()) {
            return ResponseEntity.badRequest().body(Map.of("success", false, "error", "Missing sdfName"));
        }

        Map<String, Object> responseBody = new HashMap<>();

        if (enable) {
            updateDataApp(sdfName, true);
            NipcResponse<String> response = controlClient().enableEvent(id, sdfName);
            if (!response.isSuccess()) {
                responseBody.put("success", false);
                responseBody.put("error", getErrorMessage(response));
                return ResponseEntity.badRequest().body(responseBody);
            }
            responseBody.put("success", true);
            responseBody.put("instanceId", response.getBody());
            return ResponseEntity.ok(responseBody);
        }

        if (instanceId == null || instanceId.isBlank()) {
            return ResponseEntity.badRequest().body(Map.of("success", false, "error", "Missing instanceId"));
        }

        NipcResponse<Void> response = controlClient().disableEvent(id, instanceId);
        if (!response.isSuccess()) {
            responseBody.put("success", false);
            responseBody.put("error", getErrorMessage(response));
            return ResponseEntity.badRequest().body(responseBody);
        }

        updateDataApp(sdfName, false);
        responseBody.put("success", true);
        return ResponseEntity.ok(responseBody);
    }

    private void updateDataApp(String eventName, boolean enable) throws Exception {
        var dataEndpoint = tiedieClientManager.getDataEndpointApp();
        if (dataEndpoint == null || dataEndpoint.getId() == null) {
            return;
        }

        String dataAppEndpointId = dataEndpoint.getId();
        ControlClient controlClient = controlClient();
        NipcResponse<DataAppRegistration> currentResponse = controlClient.getDataApp(dataAppEndpointId);

        DataAppRegistration registration;
        if (!currentResponse.isSuccess() || currentResponse.getBody() == null) {
            registration = createDataAppRegistration(List.of(eventName));
            controlClient.createDataApp(dataAppEndpointId, registration);
            return;
        }

        DataAppRegistration current = currentResponse.getBody();
        List<Event> events = current.getEvents() == null
                ? new ArrayList<>()
                : new ArrayList<>(current.getEvents());

        if (enable) {
            boolean alreadyExists = events.stream().anyMatch(event -> eventName.equals(event.getEvent()));
            if (!alreadyExists) {
                Event event = new Event();
                event.setEvent(eventName);
                events.add(event);
            }
        } else {
            events.removeIf(event -> eventName.equals(event.getEvent()));
        }

        if (events.isEmpty()) {
            controlClient.deleteDataApp(dataAppEndpointId);
            return;
        }

        DataAppRegistration update = new DataAppRegistration();
        update.setEvents(events);
        update.setMqttClient(current.getMqttClient());
        update.setMqttBroker(current.getMqttBroker());
        controlClient.updateDataApp(dataAppEndpointId, update);
    }

    private DataAppRegistration createDataAppRegistration(List<String> eventNames) throws Exception {
        DataAppRegistration registration = new DataAppRegistration();
        List<Event> events = eventNames.stream()
                .map(name -> {
                    Event event = new Event();
                    event.setEvent(name);
                    return event;
                })
                .collect(Collectors.toList());
        registration.setEvents(events);

        if ("broker".equalsIgnoreCase(tiedieClientManager.getDataAppMqttType())) {
            registration.setMqttClient(false);

            MqttBrokerConfig brokerConfig = new MqttBrokerConfig();
            brokerConfig.setUri(tiedieClientManager.getDataAppBaseUrl());
            brokerConfig.setUsername(tiedieClientManager.getDataAppUsername());
            brokerConfig.setPassword(tiedieClientManager.getDataAppPassword());

            String brokerCaPath = tiedieClientManager.getDataAppBrokerCaPath();
            if (brokerCaPath != null && !brokerCaPath.isBlank()) {
                brokerConfig.setBrokerCACert(Files.readString(Path.of(brokerCaPath), StandardCharsets.UTF_8));
            }
            registration.setMqttBroker(brokerConfig);
        } else {
            registration.setMqttClient(true);
            registration.setMqttBroker(null);
        }

        return registration;
    }

    private Device buildDeviceFromForm(
            String deviceId,
            String displayName,
            boolean active,
            String deviceMacAddress,
            List<String> versionSupport,
            boolean isRandom,
            boolean mobility,
            String pairingMethod,
            String passKey
    ) throws Exception {
        BleExtension.Builder bleBuilder = BleExtension.builder()
                .deviceMacAddress(deviceMacAddress)
                .versionSupport(versionSupport == null ? List.of() : versionSupport)
                .isRandom(isRandom)
                .mobility(mobility);

        String normalizedPairing = pairingMethod == null ? "null" : pairingMethod;
        switch (normalizedPairing) {
            case "justWorks" -> bleBuilder.pairingJustWorks(new BleExtension.PairingJustWorks(0));
            case "passKey" -> {
                if (passKey != null && !passKey.isBlank()) {
                    bleBuilder.pairingPassKey(new BleExtension.PairingPassKey(Integer.parseInt(passKey)));
                }
            }
            default -> bleBuilder.nullPairing(new BleExtension.NullPairing(null));
        }

        Device device = Device.builder()
                .id(deviceId)
                .displayName(displayName)
                .active(active)
                .bleExtension(bleBuilder.build())
                .build();

        List<com.cisco.tiedie.dto.scim.EndpointApp> endpointApps = tiedieClientManager.getDeviceEndpointApps();
        if (!endpointApps.isEmpty()) {
            device.setEndpointAppsExtension(new EndpointAppsExtension(endpointApps));
        }

        return device;
    }

    private List<BleService> parseServiceUUIDs(String serviceUUIDs) {
        if (serviceUUIDs == null || serviceUUIDs.isBlank()) {
            return List.of();
        }

        return List.of(serviceUUIDs.split(",")).stream()
                .map(String::trim)
                .filter(value -> !value.isBlank())
                .map(BleService::new)
                .collect(Collectors.toList());
    }

    private String resolveSdfName(SdfModel sdfModel) {
        if (sdfModel == null || sdfModel.getNamespace() == null || sdfModel.getDefaultNamespace() == null) {
            throw new IllegalArgumentException("Invalid SDF model");
        }

        String namespace = sdfModel.getNamespace().get(sdfModel.getDefaultNamespace());
        if (namespace == null || namespace.isBlank()) {
            throw new IllegalArgumentException("SDF namespace is missing");
        }

        if (sdfModel.getSdfThing() != null && !sdfModel.getSdfThing().isEmpty()) {
            return namespace + "#/" + sdfModel.getSdfThing().keySet().iterator().next();
        }

        if (sdfModel.getSdfObject() != null && !sdfModel.getSdfObject().isEmpty()) {
            return namespace + "#/" + sdfModel.getSdfObject().keySet().iterator().next();
        }

        return namespace;
    }

    private String error(Model model, String message) {
        model.addAttribute("error", message);
        return "error";
    }

    private String getErrorMessage(NipcResponse<?> response) {
        if (response == null) {
            return "Unknown control error";
        }

        if (response.getError() != null && response.getError().getDetail() != null) {
            return response.getError().getDetail();
        }

        if (response.getHttp() != null && response.getHttp().getStatusMessage() != null) {
            return response.getHttp().getStatusMessage();
        }

        return "Unknown control error";
    }

    private OnboardingClient onboardingClient() throws Exception {
        return tiedieClientManager.getOnboardingClient();
    }

    private ControlClient controlClient() throws Exception {
        return tiedieClientManager.getControlClient();
    }
}
