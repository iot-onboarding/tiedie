// Copyright (c) 2023, Cisco Systems, Inc. and/or its affiliates.
// All rights reserved.
// See LICENSE file in this distribution.
// SPDX-License-Identifier: Apache-2.0

package com.cisco.tiedie.dto.nipc;

import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonValue;

import java.util.Arrays;

/**
 * NIPC problem type URIs from the NIPC draft and Python SDK parity list.
 */
public enum NipcProblemType {
    INVALID_ID("https://www.iana.org/assignments/nipc-problem-types#invalid-id"),
    INVALID_SDF_URL("https://www.iana.org/assignments/nipc-problem-types#invalid-sdf-url"),
    EXTENSION_OPERATION_NOT_EXECUTED("https://www.iana.org/assignments/nipc-problem-types#extension-operation-not-executed"),
    SDF_MODEL_ALREADY_REGISTERED("https://www.iana.org/assignments/nipc-problem-types#sdf-model-already-registered"),
    SDF_MODEL_IN_USE("https://www.iana.org/assignments/nipc-problem-types#sdf-model-in-use"),
    PROPERTY_NOT_READABLE("https://www.iana.org/assignments/nipc-problem-types#property-not-readable"),
    PROPERTY_NOT_WRITABLE("https://www.iana.org/assignments/nipc-problem-types#property-not-writable"),
    EVENT_ALREADY_ENABLED("https://www.iana.org/assignments/nipc-problem-types#event-already-enabled"),
    EVENT_NOT_ENABLED("https://www.iana.org/assignments/nipc-problem-types#event-not-enabled"),
    EVENT_NOT_REGISTERED("https://www.iana.org/assignments/nipc-problem-types#event-not-registered"),
    PROTOCOLMAP_BLE_ALREADY_CONNECTED("https://www.iana.org/assignments/nipc-problem-types#protocolmap-ble-already-connected"),
    PROTOCOLMAP_BLE_NO_CONNECTION("https://www.iana.org/assignments/nipc-problem-types#protocolmap-ble-no-connection"),
    PROTOCOLMAP_BLE_CONNECTION_TIMEOUT("https://www.iana.org/assignments/nipc-problem-types#protocolmap-ble-connection-timeout"),
    PROTOCOLMAP_BLE_BONDING_FAILED("https://www.iana.org/assignments/nipc-problem-types#protocolmap-ble-bonding-failed"),
    PROTOCOLMAP_BLE_CONNECTION_FAILED("https://www.iana.org/assignments/nipc-problem-types#protocolmap-ble-connection-failed"),
    PROTOCOLMAP_BLE_SERVICE_DISCOVERY_FAILED("https://www.iana.org/assignments/nipc-problem-types#protocolmap-ble-service-discovery-failed"),
    PROTOCOLMAP_BLE_INVALID_SERVICE_OR_CHARACTERISTIC("https://www.iana.org/assignments/nipc-problem-types#protocolmap-ble-invalid-service-or-characteristic"),
    PROTOCOLMAP_ZIGBEE_CONNECTION_TIMEOUT("https://www.iana.org/assignments/nipc-problem-types#protocolmap-zigbee-connection-timeout"),
    PROTOCOLMAP_ZIGBEE_INVALID_ENDPOINT_OR_CLUSTER("https://www.iana.org/assignments/nipc-problem-types#protocolmap-zigbee-invalid-endpoint-or-cluster"),
    EXTENSION_BROADCAST_INVALID_DATA("https://www.iana.org/assignments/nipc-problem-types#extension-broadcast-invalid-data"),
    EXTENSION_FIRMWARE_ROLLBACK("https://www.iana.org/assignments/nipc-problem-types#extension-firmware-rollback"),
    EXTENSION_FIRMWARE_UPDATE_FAILED("https://www.iana.org/assignments/nipc-problem-types#extension-firmware-update-failed"),
    ABOUT_BLANK("about:blank");

    private final String value;

    NipcProblemType(String value) {
        this.value = value;
    }

    @JsonValue
    public String getValue() {
        return value;
    }

    @JsonCreator
    public static NipcProblemType fromValue(String value) {
        if (value == null) {
            return ABOUT_BLANK;
        }

        return Arrays.stream(values())
                .filter(type -> type.value.equals(value))
                .findFirst()
                .orElse(ABOUT_BLANK);
    }
}
