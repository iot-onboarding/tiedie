// Copyright (c) 2023, Cisco and/or its affiliates.
// All rights reserved.
// See license in distribution for details.

package com.cisco.tiedie.dto.scim;

import com.fasterxml.jackson.annotation.JsonProperty;

public enum EndpointAppType {
    @JsonProperty("telemetry")
    TELEMETRY,
    @JsonProperty("deviceControl")
    DEVICE_CONTROL
}