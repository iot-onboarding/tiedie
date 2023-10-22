// Copyright (c) 2023, Cisco and/or its affiliates.
// All rights reserved.
// See license in distribution for details.

package com.cisco.tiedie.dto.control.ble;

import com.fasterxml.jackson.annotation.JsonProperty;

public enum BleAdvertisementFilterType {
    @JsonProperty("allow")
    ALLOW,
    @JsonProperty("deny")
    DENY
}