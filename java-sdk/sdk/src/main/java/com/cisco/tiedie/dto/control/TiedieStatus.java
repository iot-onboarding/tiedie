// Copyright (c) 2023, Cisco and/or its affiliates.
// All rights reserved.
// See license in distribution for details.

package com.cisco.tiedie.dto.control;

import com.fasterxml.jackson.annotation.JsonProperty;

public enum TiedieStatus {
    @JsonProperty("SUCCESS") SUCCESS,
    @JsonProperty("FAILURE") FAILURE
}
