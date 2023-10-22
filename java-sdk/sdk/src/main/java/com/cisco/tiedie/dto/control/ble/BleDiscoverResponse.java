// Copyright (c) 2023, Cisco and/or its affiliates.
// All rights reserved.
// See license in distribution for details.

package com.cisco.tiedie.dto.control.ble;

import com.cisco.tiedie.dto.control.DataParameter;
import lombok.Data;

import java.util.ArrayList;
import java.util.List;

@Data
public class BleDiscoverResponse {
    private List<BleService> services;

    public List<DataParameter> toParameterList(String deviceId) {
        List<DataParameter> parameters = new ArrayList<>();

        for (BleService service : services) {
            for (BleCharacteristic characteristic : service.characteristics) {
                var parameter = new BleDataParameter();
                parameter.setDeviceId(deviceId);
                parameter.setServiceUUID(service.uuid);
                parameter.setCharUUID(characteristic.uuid);
                parameter.setFlags(characteristic.flags);
                parameters.add(parameter);
            }
        }

        return parameters;
    }

    @Data
    private static class BleService {
        private String uuid;
        private List<BleCharacteristic> characteristics;
    }

    @Data
    private static class BleCharacteristic {
        private String uuid;
        private List<String> flags;
        private List<BleDescriptors> descriptors;
    }

    @Data
    private static class BleDescriptors {
        private String uuid;
    }
}
