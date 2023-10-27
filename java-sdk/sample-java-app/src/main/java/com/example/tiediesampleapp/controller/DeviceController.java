// Copyright (c) 2023, Cisco and/or its affiliates.
// All rights reserved.
// See LICENSE file in this distribution.
// SPDX-License-Identifier: Apache-2.0

package com.example.tiediesampleapp.controller;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.stream.Collectors;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.ModelAttribute;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.ResponseBody;

import com.cisco.tiedie.clients.ControlClient;
import com.cisco.tiedie.clients.OnboardingClient;
import com.cisco.tiedie.dto.HttpResponse;
import com.cisco.tiedie.dto.control.AdvertisementRegistrationOptions;
import com.cisco.tiedie.dto.control.ConnectionRegistrationOptions;
import com.cisco.tiedie.dto.control.DataFormat;
import com.cisco.tiedie.dto.control.DataParameter;
import com.cisco.tiedie.dto.control.DataRegistrationOptions;
import com.cisco.tiedie.dto.control.DataResponse;
import com.cisco.tiedie.dto.control.TiedieResponse;
import com.cisco.tiedie.dto.control.ble.BleConnectRequest;
import com.cisco.tiedie.dto.control.ble.BleDataParameter;
import com.cisco.tiedie.dto.control.ble.BleService;
import com.cisco.tiedie.dto.scim.Device;
import com.cisco.tiedie.dto.scim.EndpointAppsExtension;
import com.example.tiediesampleapp.model.AdvertisementRequest;

@Controller
public class DeviceController {

    @Autowired
    OnboardingClient onboardingClient;

    @Autowired
    ControlClient controlClient;

    // @Autowired
    // @Qualifier("controlApp")
    // private EndpointApp controlApp;

    // @Autowired
    // @Qualifier("dataApp")
    // private EndpointApp dataApp;

    @Value("${onboarding-app.id}")
    private String onboardingAppId;

    @Value("${control-app.id}")
    private String controlAppId;

    @Value("${data-app.id}")
    private String dataAppId;

    private Set<String> subscriptionTopics = new HashSet<>();

    private Set<String> advertisementTopics = new HashSet<>();

    @GetMapping("/")
    public String index() throws Exception {
        return "devices";
    }

    @GetMapping("/devices")
    public String getAllDevices(Model model) throws Exception {
        return "devices";
    }

    @GetMapping("/subscriptions")
    public String getSubscriptions(Model model) throws Exception {
        model.addAttribute("subscriptionTopics", subscriptionTopics);
        model.addAttribute("advertisementTopics", advertisementTopics);
        return "subscriptions";
    }

    @GetMapping("/subscription")
    public String getSubscriptions(Model model, @RequestParam("topic") String topic) throws Exception {
        model.addAttribute("topic", topic);
        return "subscription";
    }

    @GetMapping("/advertisement")
    public String getAdvertisements(Model model, @RequestParam("topic") String topic) throws Exception {
        model.addAttribute("topic", topic);
        return "advertisement";
    }

    @GetMapping("/devices/add")
    public String addDevice(Model model) throws Exception {
        model.addAttribute("device", new Device());
        return "device_add";
    }

    @PostMapping("/devices/add")
    public String addDevice(@ModelAttribute Device device, Model model) throws Exception {
        System.out.println(device);
        device.setEndpointAppsExtension(EndpointAppsExtension.builder()
                .onboardingUrl(onboardingAppId)
                .deviceControlUrl(List.of(controlAppId))
                .dataReceiverUrl(List.of(dataAppId))
                .build());
        HttpResponse<Device> response = onboardingClient.createDevice(device);

        if (response.getStatusCode() != 200 && response.getStatusCode() != 201) {
            model.addAttribute("error", "Failed to create device");
            return "error";
        }

        String topic = "data-app/" + response.getBody().getId() + "/connection";

        TiedieResponse<Void> dataAppResponse = controlClient.registerDataApp(dataAppId, topic);

        if (dataAppResponse.getHttpStatusCode() != 200) {
            model.addAttribute("error", dataAppResponse.getHttpMessage());
            return "error";
        }

        controlClient.registerTopic(topic, ConnectionRegistrationOptions.builder()
                .dataFormat(DataFormat.DEFAULT)
                .devices(List.of(response.getBody()))
                .build());

        return "redirect:/devices/" + response.getBody().getId();
    }

    @GetMapping("/devices/{id}")
    public String getDevice(Model model, @PathVariable("id") String id) throws Exception {
        HttpResponse<Device> response = onboardingClient.getDevice(id);

        if (response.getStatusCode() != 200) {
            model.addAttribute("error", "Failed to get device");
            return "error";
        }

        Device device = response.getBody();
        model.addAttribute("device", device);

        TiedieResponse<List<DataParameter>> dataResponse = controlClient.discover(device,
                List.of(new BleDataParameter("1800")));

        if (dataResponse.getHttpStatusCode() != 200) {
            return "device";
        }

        System.out.println(dataResponse.getBody());
        List<BleDataParameter> bleDataParameters = dataResponse
                .getBody()
                .stream()
                .filter(BleDataParameter.class::isInstance)
                .map(BleDataParameter.class::cast)
                .collect(Collectors.toList());

        model.addAttribute("parameters", bleDataParameters);

        return "device";
    }

    @PostMapping("/devices/{id}/connect")
    public String connectDevice(@ModelAttribute Device device, Model model, @RequestParam String serviceUUIDs)
            throws Exception {
        String[] uuids = serviceUUIDs.split(",");
        List<BleService> services = new ArrayList<>();
        for (String uuid : uuids) {
            services.add(new BleService(uuid));
        }

        TiedieResponse<List<DataParameter>> response = controlClient.connect(device,
                BleConnectRequest.builder()
                        .services(services)
                        .build());

        if (response.getHttpStatusCode() != 200) {
            return "error";
        }

        return "redirect:/devices/{id}";
    }

    @PostMapping("/devices/{id}/disconnect")
    public String disconnectDevice(@ModelAttribute Device device, Model model) throws Exception {
        TiedieResponse<Void> response = controlClient.disconnect(device);

        if (response.getHttpStatusCode() != 200) {
            return "error";
        }

        return "redirect:/devices/{id}";
    }

    @PostMapping("/devices/{id}/delete")
    public String deleteDevice(@PathVariable("id") String id, Model model) throws Exception {
        HttpResponse<Void> response = onboardingClient.deleteDevice(id);

        if (response.getStatusCode() != 200 && response.getStatusCode() != 204) {
            return "error";
        }

        return "redirect:/devices";
    }

    @PostMapping("/devices/{id}/advertisements")
    public String subscribeAdvertisements(@PathVariable("id") String id, Model model) throws Exception {
        HttpResponse<Device> response = onboardingClient.getDevice(id);

        if (response.getStatusCode() != 200) {
            model.addAttribute("error", "Failed to get device");
            return "error";
        }

        String topic = "data-app/" + id + "/advertisements";
        TiedieResponse<Void> dataAppResponse = controlClient.registerDataApp(dataAppId, topic);

        if (dataAppResponse.getHttpStatusCode() != 200) {
            model.addAttribute("error", dataAppResponse.getHttpMessage());
            return "error";
        }

        TiedieResponse<Void> topicResponse = controlClient.registerTopic(topic,
                AdvertisementRegistrationOptions.builder()
                        .devices(List.of(response.getBody()))
                        .dataFormat(DataFormat.DEFAULT)
                        .build());

        if (topicResponse.getHttpStatusCode() != 200) {
            model.addAttribute("error", topicResponse.getHttpMessage());
            return "error";
        }

        advertisementTopics.add(topic);

        return "redirect:/advertisement?topic=" + topic;
    }

    @PostMapping("/unsubscribe")
    public String unsubscribe(@RequestParam("topic") String topic, Model model) throws Exception {
        String[] parts = topic.split("/");
        String id = parts[1];

        List<String> ids = null;

        if (!id.equals("advertisements")) {
            ids = List.of(id);
        }

        TiedieResponse<Void> response = controlClient.unregisterTopic(topic, ids);

        if (response.getHttpStatusCode() != 200) {
            model.addAttribute("error", response.getHttpMessage());
            return "error";
        }

        subscriptionTopics.remove(topic);
        advertisementTopics.remove(topic);

        return "redirect:/subscriptions";
    }

    @PostMapping(value = "/devices/{id}/svc/{svcUUID}/char/{charUUID}/read", produces = "application/json")
    @ResponseBody
    public DataResponse readCharacteristic(@PathVariable("id") String id,
            @PathVariable("svcUUID") String svcUUID,
            @PathVariable("charUUID") String charUUID,
            Model model) throws Exception {
        BleDataParameter parameter = new BleDataParameter(id, svcUUID, charUUID);

        TiedieResponse<DataResponse> response = controlClient.read(parameter);

        return response.getBody();
    }

    @PostMapping(value = "/devices/{id}/svc/{svcUUID}/char/{charUUID}/write", produces = "application/json")
    @ResponseBody
    public DataResponse writeCharacteristic(@PathVariable("id") String id,
            @PathVariable("svcUUID") String svcUUID,
            @PathVariable("charUUID") String charUUID,
            @RequestBody String value,
            Model model) throws Exception {
        BleDataParameter parameter = new BleDataParameter(id, svcUUID, charUUID);

        TiedieResponse<DataResponse> response = controlClient.write(parameter, value);

        System.out.println(response.getBody());

        return response.getBody();
    }

    @PostMapping(value = "/devices/{id}/svc/{svcUUID}/char/{charUUID}/subscribe", produces = "application/json")
    @ResponseBody
    public Map<String, String> subscribeCharacteristic(@PathVariable("id") String id,
            @PathVariable("svcUUID") String svcUUID,
            @PathVariable("charUUID") String charUUID,
            Model model) throws Exception {
        BleDataParameter parameter = new BleDataParameter(id, svcUUID, charUUID);

        String topic = "data-app/" + id + "/" + svcUUID + "/" + charUUID;

        TiedieResponse<Void> dataAppResponse = controlClient.registerDataApp(dataAppId, topic);

        Map<String, String> map = new HashMap<>();

        if (dataAppResponse.getHttpStatusCode() != 200) {
            map.put("error", dataAppResponse.getHttpMessage());
            return map;
        }

        TiedieResponse<Void> topicResponse = controlClient.registerTopic(topic, DataRegistrationOptions.builder()
                .dataFormat(DataFormat.DEFAULT)
                .dataParameter(parameter)
                .build());

        if (topicResponse.getHttpStatusCode() != 200) {
            map.put("error", dataAppResponse.getHttpMessage());
            return map;
        }

        TiedieResponse<Void> subscribe = controlClient.subscribe(parameter);

        if (subscribe.getHttpStatusCode() != 200) {
            map.put("error", dataAppResponse.getHttpMessage());
            return map;
        }

        subscriptionTopics.add(topic);

        map.put("topic", topic);

        return map;
    }

    @PostMapping(value = "/advertisements", produces = "application/json")
    @ResponseBody
    public Map<String, String> subscribeAdvertisements(@RequestBody AdvertisementRequest request, Model model)
            throws Exception {
        String topic = "data-app/advertisements/" + request.getTopic();

        TiedieResponse<Void> dataAppResponse = controlClient.registerDataApp(dataAppId, topic);

        Map<String, String> map = new HashMap<>();

        if (dataAppResponse.getHttpStatusCode() != 200) {
            map.put("error", dataAppResponse.getHttpMessage());
            return map;
        }

        TiedieResponse<Void> topicResponse = controlClient.registerTopic(topic,
                AdvertisementRegistrationOptions.builder()
                        .dataFormat(DataFormat.DEFAULT)
                        .advertisementFilterType(request.getFilterType())
                        .advertisementFilters(request.getFilters())
                        .build());

        if (topicResponse.getHttpStatusCode() != 200) {
            map.put("error", dataAppResponse.getHttpMessage());
            return map;
        }

        advertisementTopics.add(topic);

        map.put("topic", topic);

        return map;
    }
}
