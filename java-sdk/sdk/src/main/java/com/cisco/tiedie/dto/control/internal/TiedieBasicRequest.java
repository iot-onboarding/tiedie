// Copyright (c) 2023, Cisco Systems, Inc. and/or its affiliates.
// All rights reserved.
// See LICENSE file in this distribution.
// SPDX-License-Identifier: Apache-2.0

package com.cisco.tiedie.dto.control.internal;

import com.cisco.tiedie.dto.scim.Device;
import lombok.Data;

@Data
public class TiedieBasicRequest {
    private Technology technology;
    private String id;
    public static TiedieBasicRequest createRequest(Device device) {
        var tiedieRequest = new TiedieBasicRequest();
        tiedieRequest.setId(device.getId());

        if (device.getBleExtension() != null) {
            tiedieRequest.setTechnology(Technology.BLE);
        } else if (device.getZigbeeExtension() != null) {
            tiedieRequest.setTechnology(Technology.ZIGBEE);
        }

        return tiedieRequest;
    }
}
