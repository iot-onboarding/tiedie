// Copyright (c) 2023, Cisco and/or its affiliates.
// All rights reserved.
// See license in distribution for details.

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
public class TiedieUnsubscribeRequest extends TiedieBasicRequest {
    private BleUnsubscribeRequest ble;
    private ZigbeeUnsubscribeRequest zigbee;

    public static TiedieUnsubscribeRequest createRequest(DataParameter dataParameter, String controlAppId) {
        if (dataParameter instanceof BleDataParameter) {
            BleDataParameter bleDataParameter = (BleDataParameter) dataParameter;

            return createRequest(bleDataParameter, controlAppId);
        }

        if (dataParameter instanceof ZigbeeDataParameter) {
            ZigbeeDataParameter zigbeeDataParameter = (ZigbeeDataParameter) dataParameter;

            return createRequest(zigbeeDataParameter, controlAppId);
        }

        throw new UnsupportedOperationException("Operation not supported for this device");
    }

    public static TiedieUnsubscribeRequest createRequest(BleDataParameter dataParameter, String controlAppId) {
        var tiedieRequest = new TiedieUnsubscribeRequest();
        tiedieRequest.setId(dataParameter.getDeviceId());
        tiedieRequest.setControlApp(controlAppId);

        tiedieRequest.setTechnology(Technology.BLE);

        var bleSubscribeRequest = new BleUnsubscribeRequest(dataParameter.getServiceUUID(), dataParameter.getCharUUID());

        tiedieRequest.setBle(bleSubscribeRequest);

        return tiedieRequest;
    }

    private static TiedieUnsubscribeRequest createRequest(ZigbeeDataParameter dataParameter, String controlAppId) {
        var tiedieRequest = new TiedieUnsubscribeRequest();
        tiedieRequest.setId(dataParameter.getDeviceId());
        tiedieRequest.setControlApp(controlAppId);

        tiedieRequest.setTechnology(Technology.ZIGBEE);

        var zigbeeSubscribeRequest = new ZigbeeUnsubscribeRequest(
                dataParameter.getEndpointID(),
                dataParameter.getClusterID(),
                dataParameter.getAttributeID(),
                dataParameter.getType());

        tiedieRequest.setZigbee(zigbeeSubscribeRequest);

        return tiedieRequest;
    }

    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    private static class BleUnsubscribeRequest {
        private String serviceID;
        private String characteristicID;
    }

    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    private static class ZigbeeUnsubscribeRequest {
        private Integer endpointID;
        private Integer clusterID;
        private Integer attributeID;
        private Integer type;
    }
}
