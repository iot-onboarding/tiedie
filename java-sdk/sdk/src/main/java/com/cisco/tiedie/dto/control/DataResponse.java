// Copyright (c) 2023, Cisco and/or its affiliates.
// All rights reserved.
// See license in distribution for details.

package com.cisco.tiedie.dto.control;

import lombok.Data;

/**
 * Response from Control read/write APIs.
 */
@Data
public class DataResponse {
    /**
     * Data from the device encoded in hex.
     */
    private String value;
}
