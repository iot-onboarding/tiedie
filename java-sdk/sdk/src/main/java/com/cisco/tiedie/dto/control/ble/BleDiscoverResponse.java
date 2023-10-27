// Copyright (c) 2023, Cisco and/or its affiliates.
// All rights reserved.
// See LICENSE file in this distribution.
// SPDX-License-Identifier: Apache-2.0

package com.cisco.tiedie.dto.control.ble;

import com.cisco.tiedie.dto.control.DataParameter;
import com.fasterxml.jackson.annotation.JsonIgnoreProperties;

import lombok.Data;

import java.util.ArrayList;
import java.util.List;

@Data
@JsonIgnoreProperties(ignoreUnknown = true)
public class BleDiscoverResponse {
    private List<BleService> services;

    public List<DataParameter> toParameterList(String deviceId) {
        List<DataParameter> parameters = new ArrayList<>();

        for (BleService service : services) {
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
}
