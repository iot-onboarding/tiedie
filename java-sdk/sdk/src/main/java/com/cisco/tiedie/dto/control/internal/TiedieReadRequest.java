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

@Data
@EqualsAndHashCode(callSuper = true)
public class TiedieReadRequest extends TiedieBasicRequest {
    private BleReadRequest ble;
    private ZigbeeReadRequest zigbee;

    public static TiedieReadRequest createRequest(DataParameter dataParameter, String controlAppId) {
        var tiedieRequest = new TiedieReadRequest();
        tiedieRequest.setId(dataParameter.getDeviceId());
        tiedieRequest.setControlApp(controlAppId);

        if (dataParameter instanceof BleDataParameter) {
            BleDataParameter bleDataParameter = (BleDataParameter) dataParameter;
            tiedieRequest.setTechnology(Technology.BLE);
            var bleReadRequest = new BleReadRequest(bleDataParameter.getServiceUUID(), bleDataParameter.getCharUUID());

            tiedieRequest.setBle(bleReadRequest);
        } else if (dataParameter instanceof ZigbeeDataParameter) {
            ZigbeeDataParameter zigbeeDataParameter = (ZigbeeDataParameter) dataParameter;
            tiedieRequest.setTechnology(Technology.ZIGBEE);
            var zigbeeReadRequest = new ZigbeeReadRequest(
                    zigbeeDataParameter.getEndpointID(),
                    zigbeeDataParameter.getClusterID(),
                    zigbeeDataParameter.getAttributeID(),
                    zigbeeDataParameter.getType());

            tiedieRequest.setZigbee(zigbeeReadRequest);
        } else {
            throw new UnsupportedOperationException("Operation not supported for this device");
        }

        return tiedieRequest;
    }

    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    private static class BleReadRequest {
        private String serviceID;
        private String characteristicID;
    }

    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    private static class ZigbeeReadRequest {
        private Integer endpointID;
        private Integer clusterID;
        private Integer attributeID;
        private Integer type;
    }
}
