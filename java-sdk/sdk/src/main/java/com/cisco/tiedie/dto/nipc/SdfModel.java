// Copyright (c) 2023, Cisco Systems, Inc. and/or its affiliates.
// All rights reserved.
// See LICENSE file in this distribution.
// SPDX-License-Identifier: Apache-2.0

package com.cisco.tiedie.dto.nipc;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Data;

import java.util.Map;

@Data
@JsonIgnoreProperties(ignoreUnknown = true)
public class SdfModel {
    private Map<String, String> namespace;

    @JsonProperty("defaultNamespace")
    private String defaultNamespace;

    @JsonProperty("sdfThing")
    private Map<String, SdfThing> sdfThing;

    @JsonProperty("sdfObject")
    private Map<String, SdfObject> sdfObject;
}
