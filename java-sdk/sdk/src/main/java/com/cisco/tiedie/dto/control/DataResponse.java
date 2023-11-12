// Copyright (c) 2023, Cisco Systems, Inc. and/or its affiliates.
// All rights reserved.
// See LICENSE file in this distribution.
// SPDX-License-Identifier: Apache-2.0

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
