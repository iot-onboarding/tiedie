// Copyright (c) 2023, Cisco and/or its affiliates.
// All rights reserved.
// See LICENSE file in this distribution.
// SPDX-License-Identifier: Apache-2.0

package com.cisco.tiedie.dto.scim;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.extern.jackson.Jacksonized;

import java.util.List;

/**
 * A schema that extends the device schema to enable the provisioning of Zigbee devices.
 * <p>
 * The extension is identified using the following schema URI:
 * <p>
 * urn:ietf:params:scim:schemas:extension:zigbee:2.0:Device
 */
@Data
@AllArgsConstructor
@NoArgsConstructor
@Jacksonized
@Builder(builderClassName = "Builder")
public class ZigbeeExtension {
    /**
     * An array of strings of all the Zigbee versions supported by the device.
     * This attribute is required, case-insensitive, mutable, and returned by default.
     */
    private List<String> versionSupport;

    /**
     * An EUI-64 (Extended Unique Identifier) device address stored as string.
     * This attribute is required, case-insensitive, mutable, and returned by default.
     * <p>
     * The regex pattern is as follows:
     * <p>
     * ^[0-9A-Fa-f]{16}$
     */
    private String deviceEui64Address;
}
