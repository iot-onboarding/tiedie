// Copyright (c) 2023, Cisco Systems, Inc. and/or its affiliates.
// All rights reserved.
// See LICENSE file in this distribution.
// SPDX-License-Identifier: Apache-2.0

package com.cisco.tiedie.dto.scim;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.extern.jackson.Jacksonized;

import java.util.ArrayList;
import java.util.List;

@Data
@AllArgsConstructor
@NoArgsConstructor
@Jacksonized
@Builder(builderClassName = "Builder")
public class EndpointAppsExtension {
    private List<Application> applications;
    private String deviceControlEnterpriseEndpoint;
    private String telemetryEnterpriseEndpoint;

    public EndpointAppsExtension(List<EndpointApp> applications) {
        this.applications = new ArrayList<>();
        for (EndpointApp app : applications) {
            this.applications.add(Application.builder()
                    .value(app.getId())
                    .build());
        }
    }

    @Data
    @AllArgsConstructor
    @NoArgsConstructor
    @Jacksonized
    @lombok.Builder(builderClassName = "Builder")
    static class Application {
        private String value;
        @JsonProperty("$ref")
        private String ref;
    }
}
