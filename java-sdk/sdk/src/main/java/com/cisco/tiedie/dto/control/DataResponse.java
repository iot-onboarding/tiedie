// Copyright (c) 2023, Cisco and/or its affiliates.
// All rights reserved.
// See LICENSE file in this distribution.
// SPDX-License-Identifier: Apache-2.0

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
