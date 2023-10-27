// Copyright (c) 2023, Cisco and/or its affiliates.
// All rights reserved.
// See LICENSE file in this distribution.
// SPDX-License-Identifier: Apache-2.0

package com.cisco.tiedie.dto.control.internal;

import com.cisco.tiedie.dto.control.DataParameter;
import com.cisco.tiedie.dto.control.ble.BleDataParameter;
import com.cisco.tiedie.dto.control.zigbee.ZigbeeDataParameter;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.EqualsAndHashCode;
import lombok.NoArgsConstructor;

import java.util.ArrayList;
import java.util.List;

@Data
@EqualsAndHashCode(callSuper = true)
public class TiedieWriteRequest extends TiedieBasicRequest {
    private BleWriteRequest ble;
    private ZigbeeWriteRequest zigbee;

    public static TiedieWriteRequest createRequest(DataParameter dataParameter, String value, String controlAppId) {
        var tiedieRequest = new TiedieWriteRequest();
        tiedieRequest.setUuid(dataParameter.getDeviceId());
        tiedieRequest.setControlApp(controlAppId);

        if (dataParameter instanceof BleDataParameter) {
            BleDataParameter bleDataParameter = (BleDataParameter) dataParameter;
            tiedieRequest.setTechnology(Technology.BLE);
            var bleWriteRequest = new BleWriteRequest(bleDataParameter.getServiceUUID(), bleDataParameter.getCharUUID(), value);

            tiedieRequest.setBle(bleWriteRequest);
        } else if (dataParameter instanceof ZigbeeDataParameter) {
            List<Integer> bytes = new ArrayList<>();
            for (int i = 0; i < value.length(); i += 2) {
                String s = value.substring(i, i + 2);
                bytes.add(Integer.parseInt(s, 16));
            }
            ZigbeeDataParameter zigbeeDataParameter = (ZigbeeDataParameter) dataParameter;
            tiedieRequest.setTechnology(Technology.ZIGBEE);
            var zigbeeWriteRequest = new ZigbeeWriteRequest(
                    zigbeeDataParameter.getEndpointID(),
                    zigbeeDataParameter.getClusterID(),
                    zigbeeDataParameter.getAttributeID(),
                    zigbeeDataParameter.getType(),
                    bytes);

            tiedieRequest.setZigbee(zigbeeWriteRequest);
        } else {
            throw new UnsupportedOperationException("Operation not supported for this device");
        }

        return tiedieRequest;
    }

    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    private static class BleWriteRequest {
        private String serviceUUID;
        private String characteristicUUID;
        private String value;
    }

    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    private static class ZigbeeWriteRequest {
        private Integer endpointID;
        private Integer clusterID;
        private Integer attributeID;
        private Integer type;
        private List<Integer> data;
    }
}
