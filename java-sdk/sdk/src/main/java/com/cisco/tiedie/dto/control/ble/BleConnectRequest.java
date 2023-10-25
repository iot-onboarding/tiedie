// Copyright (c) 2023, Cisco and/or its affiliates.
// All rights reserved.
// See license in distribution for details.

package com.cisco.tiedie.dto.control.ble;

import java.util.List;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * BLE Connection options
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class BleConnectRequest {
    /**
     * Optional list of services to be discoveered
     */
    private List<BleService> services;
    /**
     * Number of times to retry the connect request at the AP.
     */
    @Builder.Default
    private int retries = 3;

    /**
     * Flag to retry the connect request at multiple APs.
     */
    private boolean retryMultipleAPs;
}
