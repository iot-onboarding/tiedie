package com.cisco.tiedie.dto.telemetry;

import lombok.Data;

@Data
public class BleConnectionStatus {
    String macAddress;
    boolean connected;
    int reason;
}
