package com.cisco.tiedie.dto.control.ble;

import java.util.List;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;

import lombok.Data;

@Data
@JsonIgnoreProperties(ignoreUnknown = true)
public class BleCharacteristic {
        private String characteristicID;
        private List<String> flags;
        private List<BleDescriptors> descriptors;
}
