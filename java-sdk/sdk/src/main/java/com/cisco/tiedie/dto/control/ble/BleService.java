package com.cisco.tiedie.dto.control.ble;

import java.util.List;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@NoArgsConstructor
@AllArgsConstructor
@JsonIgnoreProperties(ignoreUnknown = true)
public class BleService {
    private String serviceID;
    private List<BleCharacteristic> characteristics;

    public BleService(String serviceID) {
        this.serviceID = serviceID;
    }
}
