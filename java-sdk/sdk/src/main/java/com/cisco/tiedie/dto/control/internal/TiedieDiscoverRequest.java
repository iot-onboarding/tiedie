// Copyright (c) 2023, Cisco and/or its affiliates.
// All rights reserved.
// See license in distribution for details.

package com.cisco.tiedie.dto.control.internal;

import java.util.ArrayList;
import java.util.List;

import com.cisco.tiedie.dto.control.DataParameter;
import com.cisco.tiedie.dto.control.ble.BleDataParameter;
import com.cisco.tiedie.dto.control.ble.BleDiscoverRequest;
import com.cisco.tiedie.dto.control.ble.BleService;
import com.cisco.tiedie.dto.scim.Device;
import lombok.Data;
import lombok.EqualsAndHashCode;

@Data
@EqualsAndHashCode(callSuper = true)
public class TiedieDiscoverRequest extends TiedieBasicRequest {

    private BleDiscoverRequest ble;

    public static TiedieDiscoverRequest createRequest(Device device, List<DataParameter> parameters,
            String controlAppId) {
        TiedieDiscoverRequest tiedieRequest = new TiedieDiscoverRequest();
        tiedieRequest.setId(device.getId());
        tiedieRequest.setControlApp(controlAppId);

        if (device.getBleExtension() != null) {
            tiedieRequest.setTechnology(Technology.BLE);
            List<BleService> services = new ArrayList<>();
            if (parameters != null) {
                for (var parameter : parameters) {
                    if (parameter instanceof BleDataParameter) {
                        var bleParameter = (BleDataParameter) parameter;
                        services.add(new BleService(bleParameter.getServiceUUID()));
                    }
                }
            }
            tiedieRequest.setBle(new BleDiscoverRequest(services));
        } else if (device.getZigbeeExtension() != null) {
            tiedieRequest.setTechnology(Technology.ZIGBEE);
        }

        return tiedieRequest;
    }

}
