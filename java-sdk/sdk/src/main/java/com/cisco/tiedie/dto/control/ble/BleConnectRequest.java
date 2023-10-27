// Copyright (c) 2023, Cisco and/or its affiliates.
// All rights reserved.
// See LICENSE file in this distribution.
// SPDX-License-Identifier: Apache-2.0

package com.cisco.tiedie.dto.control.ble;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * BLE Connection options
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
public class BleConnectRequest {
    /**
     * Number of times to retry the connect request at the AP.
     */
    private int retries;

    /**
     * Flag to retry the connect request at multiple APs.
     */
    private boolean retryMultipleAPs;
}
