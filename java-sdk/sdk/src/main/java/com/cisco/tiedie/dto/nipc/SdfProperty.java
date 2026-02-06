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
public class SdfProperty {
    private String description;
    private Boolean observable;
    private Boolean readable;
    private Boolean writable;
    private String type;
    private String unit;

    @JsonProperty("sdfProtocolMap")
    private Map<String, Object> sdfProtocolMap;
}
