// Copyright (c) 2023, Cisco and/or its affiliates.
// All rights reserved.
// See LICENSE file in this distribution.
// SPDX-License-Identifier: Apache-2.0

package com.cisco.tiedie.dto.control.zigbee;

import com.cisco.tiedie.dto.control.DataParameter;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.EqualsAndHashCode;
import lombok.NoArgsConstructor;

/**
 * {@inheritDoc}
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
@EqualsAndHashCode(callSuper = true)
public class ZigbeeDataParameter extends DataParameter {
    private Integer endpointID;
    private Integer clusterID;
    private Integer attributeID;
    private Integer type;

    /**
     * Create Zigbee parameters to be used for the read/write operation.
     *
     * @param deviceId    Device ID
     * @param endpointID  Zigbee endpoint ID
     * @param clusterID   Zigbee cluster ID
     * @param attributeID Zigbee attribute ID
     * @param type        Zigbee attribute type
     */
    public ZigbeeDataParameter(String deviceId, Integer endpointID, Integer clusterID, Integer attributeID, Integer type) {
        super(deviceId);
        this.endpointID = endpointID;
        this.clusterID = clusterID;
        this.attributeID = attributeID;
        this.type = type;
    }

    /**
     * Create Zigbee parameters to be used for the read/write operation.
     *
     * @param deviceId    Device ID
     * @param endpointID  Zigbee endpoint ID
     * @param clusterID   Zigbee cluster ID
     * @param attributeID Zigbee attribute ID
     */
    public ZigbeeDataParameter(String deviceId, Integer endpointID, Integer clusterID, Integer attributeID) {
        super(deviceId);
        this.endpointID = endpointID;
        this.clusterID = clusterID;
        this.attributeID = attributeID;
    }
}