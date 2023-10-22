// Copyright (c) 2023, Cisco and/or its affiliates.
// All rights reserved.
// See license in distribution for details.

package com.cisco.tiedie.dto.control.internal;

import com.cisco.tiedie.dto.control.*;
import com.cisco.tiedie.dto.control.ble.BleAdvertisementFilter;
import com.cisco.tiedie.dto.control.ble.BleAdvertisementFilterType;
import com.cisco.tiedie.dto.control.ble.BleDataParameter;
import com.cisco.tiedie.dto.control.zigbee.ZigbeeDataParameter;
import com.cisco.tiedie.dto.scim.Device;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.annotation.JsonSubTypes;
import com.fasterxml.jackson.annotation.JsonSubTypes.Type;
import com.fasterxml.jackson.annotation.JsonTypeInfo;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.EqualsAndHashCode;
import lombok.NoArgsConstructor;

import java.util.List;
import java.util.stream.Collectors;

@Data
@EqualsAndHashCode(callSuper = true)
public class TiedieRegisterTopicRequest extends TiedieBasicRequest {
    private List<String> uuids;
    private String topic;
    private DataFormat dataFormat;

    private BleRegisterTopicRequest ble;
    private ZigbeeRegisterTopicRequest zigbee;

    public static TiedieRegisterTopicRequest createRequest(String topic, RegistrationOptions options,
                                                           String controlAppId) {
        var tiedieRequest = new TiedieRegisterTopicRequest();

        tiedieRequest.setControlApp(controlAppId);
        tiedieRequest.setTopic(topic);
        tiedieRequest.setDataFormat(options.getDataFormat());

        if (options instanceof DataRegistrationOptions) {
            DataRegistrationOptions dataRegistrationOptions = (DataRegistrationOptions) options;

            if (dataRegistrationOptions.getDataParameter() instanceof BleDataParameter) {
                BleDataParameter parameter = (BleDataParameter) dataRegistrationOptions.getDataParameter();
                tiedieRequest.setTechnology(Technology.BLE);
                tiedieRequest.setUuids(List.of(parameter.getDeviceId()));
                tiedieRequest.setBle(new BleGattTopic(parameter.getServiceUUID(), parameter.getCharUUID()));
            } else {
                ZigbeeDataParameter parameter = (ZigbeeDataParameter) dataRegistrationOptions.getDataParameter();
                tiedieRequest.setTechnology(Technology.ZIGBEE);
                tiedieRequest.setUuids(List.of(parameter.getDeviceId()));
                tiedieRequest.setZigbee(new ZigbeeRegisterTopicRequest(
                        parameter.getEndpointID(),
                        parameter.getClusterID(),
                        parameter.getAttributeID(),
                        parameter.getType()));
            }
        } else if (options instanceof AdvertisementRegistrationOptions) {
            AdvertisementRegistrationOptions advertisementRegistrationOptions = (AdvertisementRegistrationOptions) options;
            tiedieRequest.setTechnology(Technology.BLE);
            tiedieRequest.setBle(
                    new BleAdvertisementTopic(advertisementRegistrationOptions.getAdvertisementFilterType(), advertisementRegistrationOptions.getAdvertisementFilters()));

        } else if (options instanceof ConnectionRegistrationOptions) {
            tiedieRequest.setTechnology(Technology.BLE);
            tiedieRequest.setBle(new BleConnectionTopic());
        }

        if (options.getDevices() != null) {
            tiedieRequest.setUuids(options.getDevices().stream().map(Device::getId).collect(Collectors.toList()));
        }

        return tiedieRequest;
    }

    private enum BleTopicType {
        @JsonProperty("gatt")
        GATT,
        @JsonProperty("advertisements")
        ADVERTISEMENTS,
        @JsonProperty("connection")
        CONNECTION
    }

    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    @JsonTypeInfo(use = JsonTypeInfo.Id.NAME, property = "type", visible = true)
    @JsonSubTypes({
            @Type(name = "gatt", value = BleGattTopic.class),
            @Type(name = "advertisements", value = BleAdvertisementTopic.class),
            @Type(name = "connection", value = BleConnectionTopic.class)
    })
    private static class BleRegisterTopicRequest {
        private BleTopicType type;
    }

    @Data
    @NoArgsConstructor
    @EqualsAndHashCode(callSuper = true)
    private static class BleGattTopic extends BleRegisterTopicRequest {
        private String serviceUUID;
        private String characteristicUUID;

        public BleGattTopic(String serviceUUID, String characteristicUUID) {
            super(BleTopicType.GATT);
            this.serviceUUID = serviceUUID;
            this.characteristicUUID = characteristicUUID;
        }
    }

    @Data
    @EqualsAndHashCode(callSuper = true)
    private static class BleAdvertisementTopic extends BleRegisterTopicRequest {
        private BleAdvertisementFilterType filterType;
        private List<BleAdvertisementFilter> filters;

        public BleAdvertisementTopic() {
            super(BleTopicType.ADVERTISEMENTS);
        }

        public BleAdvertisementTopic(BleAdvertisementFilterType filterType, List<BleAdvertisementFilter> filters) {
            super(BleTopicType.ADVERTISEMENTS);
            this.filterType = filterType;
            this.filters = filters;
        }
    }

    @Data
    @EqualsAndHashCode(callSuper = true)
    private static class BleConnectionTopic extends BleRegisterTopicRequest {
        public BleConnectionTopic() {
            super(BleTopicType.CONNECTION);
        }
    }

    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    private static class ZigbeeRegisterTopicRequest {
        private Integer endpointID;
        private Integer clusterID;
        private Integer attributeID;
        private Integer type;
    }
}