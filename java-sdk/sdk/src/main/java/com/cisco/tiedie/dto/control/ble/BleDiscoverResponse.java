// Copyright (c) 2023, Cisco Systems, Inc. and/or its affiliates.
// All rights reserved.
// See LICENSE file in this distribution.
// SPDX-License-Identifier: Apache-2.0

package com.cisco.tiedie.dto.control.ble;

import com.cisco.tiedie.dto.control.DataParameter;
import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Data;

import java.util.ArrayList;
import java.util.List;

@Data
@JsonIgnoreProperties(ignoreUnknown = true)
public class BleDiscoverResponse {
    @JsonProperty("sdfProtocolMap")
    private BleServiceProtocolMap sdfProtocolMap;

    // Legacy fallback field to tolerate older response shapes.
    private List<BleService> services;

    public List<DataParameter> toParameterList(String deviceId) {
        List<DataParameter> parameters = new ArrayList<>();

        List<BleService> discoveredServices = services;
        if (sdfProtocolMap != null && sdfProtocolMap.ble != null) {
            discoveredServices = sdfProtocolMap.ble;
        }

        if (discoveredServices == null) {
            return parameters;
        }

        for (BleService service : discoveredServices) {
            if (service.getCharacteristics() == null) {
                continue;
            }

            for (BleCharacteristic characteristic : service.getCharacteristics()) {
                var parameter = new BleDataParameter();
                parameter.setDeviceId(deviceId);
                parameter.setServiceUUID(service.getServiceID());
                parameter.setCharUUID(characteristic.getCharacteristicID());
                parameter.setFlags(characteristic.getFlags());
                parameters.add(parameter);
            }
        }

        return parameters;
    }

    @Data
    @JsonIgnoreProperties(ignoreUnknown = true)
    private static class BleServiceProtocolMap {
        private List<BleService> ble;
    }
}
