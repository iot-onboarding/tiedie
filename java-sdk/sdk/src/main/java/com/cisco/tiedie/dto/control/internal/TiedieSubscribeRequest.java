// Copyright (c) 2023, Cisco Systems, Inc. and/or its affiliates.
// All rights reserved.
// See LICENSE file in this distribution.
// SPDX-License-Identifier: Apache-2.0

package com.cisco.tiedie.dto.control.internal;

import com.cisco.tiedie.dto.control.DataFormat;
import com.cisco.tiedie.dto.control.DataParameter;
import com.cisco.tiedie.dto.control.SubscriptionOptions;
import com.cisco.tiedie.dto.control.ble.BleDataParameter;
import com.cisco.tiedie.dto.control.zigbee.ZigbeeDataParameter;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.EqualsAndHashCode;
import lombok.NoArgsConstructor;

@Data
@EqualsAndHashCode(callSuper = true)
public class TiedieSubscribeRequest extends TiedieBasicRequest {
    private String topic;
    private DataFormat dataFormat;
    private BleSubscribeRequest ble;
    private ZigbeeSubscribeRequest zigbee;

    public static TiedieSubscribeRequest createRequest(DataParameter dataParameter, String controlAppId, SubscriptionOptions options) {
        if (dataParameter instanceof BleDataParameter) {
            BleDataParameter bleDataParameter = (BleDataParameter) dataParameter;

            return createRequest(bleDataParameter, controlAppId, options);
        }

        if (dataParameter instanceof ZigbeeDataParameter) {
            ZigbeeDataParameter zigbeeDataParameter = (ZigbeeDataParameter) dataParameter;

            return createRequest(zigbeeDataParameter, controlAppId, options);
        }

        throw new UnsupportedOperationException("Operation not supported for this device");
    }

    public static TiedieSubscribeRequest createRequest(BleDataParameter dataParameter, String controlAppId, SubscriptionOptions options) {
        var tiedieRequest = new TiedieSubscribeRequest();
        tiedieRequest.setId(dataParameter.getDeviceId());
        tiedieRequest.setControlApp(controlAppId);

        tiedieRequest.setTechnology(Technology.BLE);

        if (options == null) {
            options = new SubscriptionOptions();
        }

        tiedieRequest.setDataFormat(options.getDataFormat() == null ? DataFormat.DEFAULT : options.getDataFormat());

        tiedieRequest.setTopic(options.getTopic());

        var bleSubscribeRequest = new BleSubscribeRequest(dataParameter.getServiceUUID(), dataParameter.getCharUUID());

        tiedieRequest.setBle(bleSubscribeRequest);

        return tiedieRequest;
    }

    private static TiedieSubscribeRequest createRequest(ZigbeeDataParameter dataParameter, String controlAppId, SubscriptionOptions options) {
        var tiedieRequest = new TiedieSubscribeRequest();
        tiedieRequest.setId(dataParameter.getDeviceId());
        tiedieRequest.setControlApp(controlAppId);

        tiedieRequest.setTechnology(Technology.ZIGBEE);

        if (options == null) {
            options = new SubscriptionOptions();
        }

        tiedieRequest.setDataFormat(options.getDataFormat() == null ? DataFormat.DEFAULT : options.getDataFormat());

        tiedieRequest.setTopic(options.getTopic());

        var zigbeeSubscribeRequest = new ZigbeeSubscribeRequest(
                dataParameter.getEndpointID(),
                dataParameter.getClusterID(),
                dataParameter.getAttributeID(),
                dataParameter.getType(),
                options.getMinReportTime() == null ? 0 : options.getMinReportTime(),
                options.getMaxReportTime() == null ? 60 : options.getMaxReportTime());

        tiedieRequest.setZigbee(zigbeeSubscribeRequest);

        return tiedieRequest;
    }

    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    private static class BleSubscribeRequest {
        private String serviceID;
        private String characteristicID;
    }

    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    private static class ZigbeeSubscribeRequest {
        private Integer endpointID;
        private Integer clusterID;
        private Integer attributeID;
        private Integer type;
        private Integer minReportTime;
        private Integer maxReportTime;
    }
}
