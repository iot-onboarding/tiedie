package com.cisco.tiedie.dto.telemetry;

import lombok.Data;

@Data
public class ZigbeeSubscription {
    int endpointId;
    int clusterId;
    int attributeId;
    int attributeType;
}
