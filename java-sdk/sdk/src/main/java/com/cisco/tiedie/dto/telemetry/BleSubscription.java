package com.cisco.tiedie.dto.telemetry;

import lombok.Data;

@Data
public class BleSubscription {
    String serviceID;
    String characteristicID;
}
