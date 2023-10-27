// Copyright (c) 2023, Cisco and/or its affiliates.
// All rights reserved.
// See LICENSE file in this distribution.
// SPDX-License-Identifier: Apache-2.0

package com.cisco.tiedie.dto.control.internal;

import com.cisco.tiedie.dto.control.ble.BleConnectRequest;
import com.cisco.tiedie.dto.scim.Device;
import lombok.Data;
import lombok.EqualsAndHashCode;

@Data
@EqualsAndHashCode(callSuper = true)
public class TiedieConnectRequest extends TiedieBasicRequest {


    private BleConnectRequest ble;

    public static TiedieConnectRequest createRequest(Device device, BleConnectRequest request, String controlAppId) {
        TiedieConnectRequest tiedieRequest = new TiedieConnectRequest();
        tiedieRequest.setTechnology(Technology.BLE);
        tiedieRequest.setUuid(device.getId());
        tiedieRequest.setControlApp(controlAppId);
        tiedieRequest.setBle(request);

        return tiedieRequest;
    }

}
