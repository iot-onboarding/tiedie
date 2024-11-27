// Copyright (c) 2023, Cisco Systems, Inc. and/or its affiliates.
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
 * This class is used to represent a device in the TieDie environment.
 * This device is modelled after the <a href="https://datatracker.ietf.org/doc/draft-shahzad-scim-device-model/">SCIM devices model</a>.
 * <p>
 * To create a device:
 * <pre>{@code var device = Device.builder()
 *         .displayName("BLE Monitor")
 *         .active(false)
 *         .build();
 * }</pre>
 * <p>
 * To create a BLE device, add the BLE extension with the necessary fields:
 * <pre>{@code var device = Device.builder()
 *         .displayName("BLE Monitor")
 *         .active(false)
 *         .bleExtension(BleExtension.builder()
 *                 .deviceMacAddress("AA:BB:CC:11:22:33")
 *                 .addressType(false)
 *                 .versionSupport(Arrays.asList("4.1", "4.2", "5.0", "5.1", "5.2", "5.3"))
 *                 .pairingPassKey(new BleExtension.PairingPassKey(123456))
 *                 .build())
 *         .build();}</pre>
 * <p>
 * Similarly, use the {@link ZigbeeExtension} and {@link DppExtension} for Zigbee and DPP capable devices.
 *
 * @see <a href="https://datatracker.ietf.org/doc/draft-shahzad-scim-device-model/">SCIM devices model</a>.
 */
@Data
@AllArgsConstructor
@NoArgsConstructor
@Builder(builderClassName = "Builder")
@JsonDeserialize(builder = Device.Builder.class)
public class Device {
    private List<String> schemas;

    @JsonProperty("id")
    private String id;

    @JsonProperty("displayName")
    private String displayName;

    @JsonProperty("active")
    private boolean active;

    @JsonProperty("urn:ietf:params:scim:schemas:extension:ble:2.0:Device")
    private BleExtension bleExtension;

    @JsonProperty("urn:ietf:params:scim:schemas:extension:dpp:2.0:Device")
    private DppExtension dppExtension;

    @JsonProperty("urn:ietf:params:scim:schemas:extension:zigbee:2.0:Device")
    private ZigbeeExtension zigbeeExtension;

    @JsonProperty("urn:ietf:params:scim:schemas:extension:endpointAppsExt:2.0:Device")
    private EndpointAppsExtension endpointAppsExtension;

    /**
     * @return List of schema URNs based on the extensions present
     */
    @SuppressWarnings("unused")
    public List<String> getSchemas() {
        List<String> schemas = new ArrayList<>();
        schemas.add("urn:ietf:params:scim:schemas:core:2.0:Device");

        if (bleExtension != null) {
            schemas.add("urn:ietf:params:scim:schemas:extension:ble:2.0:Device");
        }

        if (dppExtension != null) {
            schemas.add("urn:ietf:params:scim:schemas:extension:dpp:2.0:Device");
        }

        if (zigbeeExtension != null) {
            schemas.add("urn:ietf:params:scim:schemas:extension:zigbee:2.0:Device");
        }

        if (endpointAppsExtension != null) {
            schemas.add("urn:ietf:params:scim:schemas:extension:endpointAppsExt:2.0:Device");
        }

        return schemas;
    }

    @SuppressWarnings("EmptyMethod")
    private void setSchemas(@SuppressWarnings("unused") List<String> schemas) {
    }

    /**
     * Builder class for {@link Device}
     */
    @JsonPOJOBuilder()
    @JsonIgnoreProperties(ignoreUnknown = true)
    public static class Builder {
        @SuppressWarnings("unused")
        private Builder schemas(List<String> schemas) {
            return this;
        }
    }
}
