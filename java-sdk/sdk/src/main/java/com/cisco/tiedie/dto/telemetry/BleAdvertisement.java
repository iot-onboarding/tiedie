package com.cisco.tiedie.dto.telemetry;

import lombok.Data;

@Data
public class BleAdvertisement {
    String macAddress;
    int rssi;
}
