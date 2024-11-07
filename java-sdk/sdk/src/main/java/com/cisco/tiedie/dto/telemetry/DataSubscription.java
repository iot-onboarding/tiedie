package com.cisco.tiedie.dto.telemetry;

import lombok.Data;

@Data
public class DataSubscription {
    byte[] data;
    float timestamp;
    String deviceID;
    String apMacAddress;
    BleSubscription BleSubscription;
    BleAdvertisement bleAdvertisement;
    BleConnectionStatus bleConnectionStatus;
    ZigbeeSubscription zigbeeSubscription;
    RawPayload rawPayload;
}
