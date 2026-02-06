// Copyright (c) 2023, Cisco Systems, Inc. and/or its affiliates.
// All rights reserved.
// See LICENSE file in this distribution.
// SPDX-License-Identifier: Apache-2.0

package com.cisco.tiedie.dto.nipc;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Data;

import java.util.List;

@Data
@JsonIgnoreProperties(ignoreUnknown = true)
public class DataAppRegistration {
    private List<Event> events;

    @JsonProperty("mqttClient")
    private Boolean mqttClient;

    @JsonProperty("mqttBroker")
    private MqttBrokerConfig mqttBroker;
}
