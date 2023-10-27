// Copyright (c) 2023, Cisco and/or its affiliates.
// All rights reserved.
// See LICENSE file in this distribution.
// SPDX-License-Identifier: Apache-2.0

package com.cisco.tiedie.dto.control;


import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * Additional data subscription options
 */
@Builder(builderClassName = "Builder")
@Data
@NoArgsConstructor
@AllArgsConstructor
public class SubscriptionOptions {
    /**
     * Topic to subscribe on
     */
    private String topic;

    /**
     * Data format of the subscription payload
     */
    private DataFormat dataFormat;

    /**
     * Minimum time for reporting values from zigbee attributes.
     * <p>
     * This is specifically used for Zigbee devices.
     */
    private Integer minReportTime;

    /**
     * Maximum time for reporting values from zigbee attributes.
     * <p>
     * This is specifically used for Zigbee devices.
     */
    private Integer maxReportTime;
}
