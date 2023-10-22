// Copyright (c) 2023, Cisco and/or its affiliates.
// All rights reserved.
// See license in distribution for details.

package com.cisco.tiedie.dto.control.ble;

import java.util.List;

import com.cisco.tiedie.dto.control.DataParameter;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.EqualsAndHashCode;
import lombok.NoArgsConstructor;

/**
 * {@inheritDoc}
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
@EqualsAndHashCode(callSuper = true)
public class BleDataParameter extends DataParameter {
    private String serviceUUID;
    private String charUUID;
    private List<String> flags;

    /**
     * Create BLE parameters to be used for the read/write operation.
     *
     * @param deviceId    Device ID
     * @param serviceUUID BLE service UUID
     * @param charUUID    BLE characteristic UUID
     */
    public BleDataParameter(String deviceId, String serviceUUID, String charUUID) {
        super(deviceId);
        this.serviceUUID = serviceUUID;
        this.charUUID = charUUID;
    }

    /**
     * Create BLE parameters to be used for the read/write operation.
     *
     * @param deviceId    Device ID
     * @param serviceUUID BLE service UUID
     * @param charUUID    BLE characteristic UUID
     * @param flags       BLE characteristic flags
     */
    public BleDataParameter(String deviceId, String serviceUUID, String charUUID, List<String> flags) {
        super(deviceId);
        this.serviceUUID = serviceUUID;
        this.charUUID = charUUID;
        this.flags = flags;
    }
}
