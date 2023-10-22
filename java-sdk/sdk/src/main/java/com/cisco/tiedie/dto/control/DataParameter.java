// Copyright (c) 2023, Cisco and/or its affiliates.
// All rights reserved.
// See license in distribution for details.

package com.cisco.tiedie.dto.control;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * This class is used in the TieDie control read/write APIs to represent
 * the parameters to read or write on the device.
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
public class DataParameter {
    /**
     * Unique ID of the device
     */
    private String deviceId;
}