// Copyright (c) 2023, Cisco Systems, Inc. and/or its affiliates.
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
 * A schema that extends the device schema to enable WiFi EasyConnect (otherwise known as Device Provisioning Protocol).
 * <p>
 * The extension is identified using the following schema URI:
 * <p>
 * urn:ietf:params:scim:schemas:extension:dpp:2.0:Device
 */
@Data
@AllArgsConstructor
@NoArgsConstructor
@Jacksonized
@Builder(builderClassName = "Builder")
public class DppExtension {
    /**
     * An integer that represents the version of DPP the device supports.
     * This attribute is required, case-insensitive, mutable, and returned by default.
     */
    private int dppVersion;

    /**
     * It is the array of strings of all the bootstrapping methods available on the enrollee device.
     * For example, [QR, NFC].
     * This attribute is optional, case insensitive, mutable, and returned by default.
     */
    private List<String> bootstrappingMethod;

    /**
     * A string value representing Elliptic-Curve Diffie–Hellman (ECDH) public key.
     * The base64 encoded lengths for P-256, P-384, and P-521 are 80, 96, and 120 characters.
     * This attribute is required, case-sensitive, mutable, and returned by default.
     */
    private String bootstrapKey;

    /**
     * The manufacturer assigns the MAC address stored as string. It is a unique 48-bit value.
     * This attribute is optional, case insensitive, mutable, and returned by default.
     * <p>
     * The regex pattern is as follows:
     * <p>
     * ^[0-9A-Fa-f]{2}(:[0-9A-Fa-f]{2}){5}.
     */
    private String deviceMacAddress;

    /**
     * This attribute is an array of strings of global operating class and channel shared as bootstrapping information.
     * It is formatted as class/channel. For example, ['81/1','115/36'].
     * This attribute is optional, case-insensitive, mutable, and returned by default.
     */
    private List<String> classChannel;

    /**
     * An alphanumeric serial number, stored as string, may also be passed as bootstrapping information.
     * This attribute is optional, case-insensitive, mutable, and returned by default.
     */
    private String serialNumber;
}
