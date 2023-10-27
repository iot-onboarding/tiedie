// Copyright (c) 2023, Cisco and/or its affiliates.
// All rights reserved.
// See LICENSE file in this distribution.
// SPDX-License-Identifier: Apache-2.0

package com.cisco.tiedie.dto.scim;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.databind.annotation.JsonDeserialize;
import com.fasterxml.jackson.databind.annotation.JsonPOJOBuilder;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.ArrayList;
import java.util.List;

/**
 * This schema extends the device schema to represent the devices supporting BLE.
 * <p>
 * The extension is identified using the following schema URI:
 * <p>
 * urn:ietf:params:scim:schemas:extension:ble:2.0:Device
 */
@Data
@AllArgsConstructor
@NoArgsConstructor
@Builder(builderClassName = "Builder")
@JsonDeserialize(builder = BleExtension.Builder.class)
public class BleExtension {

    /**
     * A multivalued attribute that provides all the BLE versions supported
     * by the device in the form of an array.  For example, [4.1, 4.2, 5.0,
     * 5.1, 5.2, 5.3].  It is required, mutable, and return as default.
     */
    @JsonProperty("versionSupport")
    private List<String> versionSupport;

    /**
     * A string value that represent a public MAC address assigned by the
     * manufacturer.  It is a unique 48-bit value.  It is required, case-insensitive,
     * and it is mutable and return as default.  The regex pattern is the following:
     * <p>
     * ^[0-9A-Fa-f]{2}(:[0-9A-Fa-f]{2}){5}
     */
    @JsonProperty("deviceMacAddress")
    private String deviceMacAddress;

    /**
     * A boolean flag taken from the BLE core specification, 5.3.  If FALSE,
     * the device is using a public MAC address.  If TRUE, the device uses a
     * Random address resolved using IRK.  This attribute is required, it is
     * mutable, and return by default.
     */
    @JsonProperty("isRandom")
    private boolean isRandom;

    @JsonProperty("separateBroadcastAddress")
    private List<String> separateBroadcastAddress;

    private List<String> pairingMethods;

    /**
     * A string value, Identity resolving key, which is unique for every
     * device.  It is used to resolve the random address.  It is required
     * when addressType is TRUE.  It is mutable and return by default.
     */
    @JsonProperty("irk")
    private String irk;

    /**
     * {@code nullPairing} does not have any attribute.  It allows pairing for BLE
     * devices that do not require a pairing method.
     */
    @JsonProperty("urn:ietf:params:scim:schemas:extension:pairingNull:2.0:Device")
    private NullPairing nullPairing;

    /**
     * Just works pairing method does not require a key to pair devices.
     * For completeness, the key attribute is included and is set to 'null'.
     * Key attribute is required, immutable, and return by default.
     */
    @JsonProperty("urn:ietf:params:scim:schemas:extension:pairingJustWorks:2.0:Device")
    private PairingJustWorks pairingJustWorks;

    /**
     * The pass key pairing method requires a 6-digit key to pair devices.
     * This extension has one singular integer attribute, "key", which is
     * required, mutable and returned by default.  The key pattern is as
     * follows:
     * <p>
     * ^[0-9]{6}$
     */
    @JsonProperty("urn:ietf:params:scim:schemas:extension:pairingPassKey:2.0:Device")
    private PairingPassKey pairingPassKey;

    /**
     * The out-of-band pairing method includes three singular attributes,
     * i.e., key, randomNumber, and confirmationNumber.
     */
    @JsonProperty("urn:ietf:params:scim:schemas:extension:pairingOOB:2.0:Device")
    private PairingOOB pairingOOB;

    /**
     * {@code nullPairing} does not have any attribute.  It allows pairing for BLE
     * devices that do not require a pairing method.
     */
    @Data
    @AllArgsConstructor
    @NoArgsConstructor
    public static class NullPairing {
        private String id;
    }

    /**
     * Just works pairing method does not require a key to pair devices.
     * For completeness, the key attribute is included and is set to 'null'.
     * Key attribute is required, immutable, and return by default.
     */
    @Data
    @AllArgsConstructor
    @NoArgsConstructor
    public static class PairingJustWorks {
        private int key;
    }

    /**
     * The pass key pairing method requires a 6-digit key to pair devices.
     * This extension has one singular integer attribute, "key", which is
     * required, mutable and returned by default.  The key pattern is as
     * follows:
     * <p>
     * ^[0-9]{6}$
     */
    @Data
    @AllArgsConstructor
    @NoArgsConstructor
    public static class PairingPassKey {
        private int key;
    }

    /**
     * The out-of-band pairing method includes three singular attributes,
     * i.e., key, randomNumber, and confirmationNumber.
     */
    @Data
    @AllArgsConstructor
    @NoArgsConstructor
    public static class PairingOOB {
        /**
         * The key is string value, required and received from out-of-bond
         * sources such as NFC.  It is case-sensitive, mutable, and returned by
         * default.
         */
        private String key;

        /**
         * It represents a nonce added to the key.  It is and
         * integer value that is required attribute.  It is mutable and returned
         * by default.
         */
        private Long randNumber;

        /**
         * An integer which some solutions require in RESTful
         * message exchange.  It is not required.  It is mutable and returned by
         * default if it exists.
         */
        private int confirmationNumber;
    }

    /**
     * An array of pairing methods associated with the BLE device.  The
     * pairing methods may require sub-attributes, such as key/password, for
     * the device pairing process.  To enable the scalability of pairing
     * methods in the future, they are represented as extensions to
     * incorporate various attributes that are part of the respective
     * pairing process.  Pairing method extensions are nested inside the BLE
     * extension.  It is required, case-sensitive, mutable, and returned by
     * default.
     *
     * @return An array of pairing methods associated with the BLE device.
     */
    public List<String> getPairingMethods() {
        List<String> pairingMethods = new ArrayList<>();
        if (nullPairing != null) {
            pairingMethods.add("urn:ietf:params:scim:schemas:extension:pairingNull:2.0:Device");
        }
        if (pairingJustWorks != null) {
            pairingMethods.add("urn:ietf:params:scim:schemas:extension:pairingJustWorks:2.0:Device");
        }
        if (pairingPassKey != null) {
            pairingMethods.add("urn:ietf:params:scim:schemas:extension:pairingPassKey:2.0:Device");
        }
        if (pairingOOB != null) {
            pairingMethods.add("urn:ietf:params:scim:schemas:extension:pairingOOB:2.0:Device");
        }

        return pairingMethods;
    }

    @SuppressWarnings("EmptyMethod")
    private void setPairingMethods(List<String> ignoredPairingMethods) {
    }

    /**
     * Builder class for {@link BleExtension}
     */
    @JsonPOJOBuilder()
    @JsonIgnoreProperties(ignoreUnknown = true)
    public static class Builder {
        @SuppressWarnings("EmptyMethod")
        private Builder pairingMethods(List<String> ignoredPairingMethods) {
            return this;
        }
    }
}
