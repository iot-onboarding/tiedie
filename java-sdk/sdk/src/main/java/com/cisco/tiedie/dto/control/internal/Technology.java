// Copyright (c) 2023, Cisco and/or its affiliates.
// All rights reserved.
// See license in distribution for details.

package com.cisco.tiedie.dto.control.internal;

import com.fasterxml.jackson.annotation.JsonProperty;

public enum Technology {
    @JsonProperty("ble") BLE,
    @JsonProperty("zigbee") ZIGBEE
}
