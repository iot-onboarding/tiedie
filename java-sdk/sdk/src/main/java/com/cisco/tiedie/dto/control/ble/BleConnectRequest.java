// Copyright (c) 2023, Cisco Systems, Inc. and/or its affiliates.
// All rights reserved.
// See LICENSE file in this distribution.
// SPDX-License-Identifier: Apache-2.0

package com.cisco.tiedie.dto.control.ble;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.List;

/**
 * BLE Connection options.
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
@JsonIgnoreProperties(ignoreUnknown = true)
public class BleConnectRequest {
    /**
     * Optional list of services to discover.
     */
    private List<BleService> services;

    private Boolean cached;

    @JsonProperty("cacheIdlePurge")
    private Integer cacheIdlePurge;

    @JsonProperty("autoUpdate")
    private Boolean autoUpdate;

    private BleBondingOptions bonding;
}
