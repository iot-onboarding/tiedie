package com.cisco.tiedie.dto.control.ble;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;

import lombok.Data;

@Data
@JsonIgnoreProperties(ignoreUnknown = true)
public class BleDescriptors {
    private String descriptorID;
}
