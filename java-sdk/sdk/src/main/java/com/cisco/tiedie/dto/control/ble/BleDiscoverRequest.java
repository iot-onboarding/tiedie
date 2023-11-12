// Copyright (c) 2023, Cisco Systems, Inc. and/or its affiliates.
// All rights reserved.
// See LICENSE file in this distribution.
// SPDX-License-Identifier: Apache-2.0

package com.cisco.tiedie.dto.control.ble;

import java.util.List;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * BLE Connection options
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
public class BleDiscoverRequest {
    /**
     * Optional list of services to be discoveered
     */
    private List<BleService> services;
}
