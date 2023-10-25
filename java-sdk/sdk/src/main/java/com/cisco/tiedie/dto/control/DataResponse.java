// Copyright (c) 2023, Cisco and/or its affiliates.
// All rights reserved.
// See license in distribution for details.

package com.cisco.tiedie.dto.control;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;

import lombok.Data;

/**
 * Response from Control read/write APIs.
 */
@Data
@JsonIgnoreProperties(ignoreUnknown = true)
public class DataResponse {
    /**
     * Data from the device encoded in hex.
     */
    private String value;
}
