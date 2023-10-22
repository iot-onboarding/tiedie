// Copyright (c) 2023, Cisco and/or its affiliates.
// All rights reserved.
// See license in distribution for details.

package com.cisco.tiedie.dto.control.internal;

import com.cisco.tiedie.dto.scim.Device;
import lombok.Data;

@Data
public class TiedieBasicRequest {
    private Technology technology;
    private String uuid;
    private String controlApp;

    public static TiedieBasicRequest createRequest(Device device, String controlAppId) {
        var tiedieRequest = new TiedieBasicRequest();
        tiedieRequest.setUuid(device.getId());
        tiedieRequest.setControlApp(controlAppId);

        if (device.getBleExtension() != null) {
            tiedieRequest.setTechnology(Technology.BLE);
        } else if (device.getZigbeeExtension() != null) {
            tiedieRequest.setTechnology(Technology.ZIGBEE);
        }

        return tiedieRequest;
    }
}
