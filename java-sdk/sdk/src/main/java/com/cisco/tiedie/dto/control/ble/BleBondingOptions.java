// Copyright (c) 2023, Cisco Systems, Inc. and/or its affiliates.
// All rights reserved.
// See LICENSE file in this distribution.
// SPDX-License-Identifier: Apache-2.0

package com.cisco.tiedie.dto.control.ble;

import com.fasterxml.jackson.annotation.JsonProperty;

public enum BleBondingOptions {
    @JsonProperty("default")
    DEFAULT,

    @JsonProperty("none")
    NONE,

    @JsonProperty("justworks")
    JUST_WORKS,

    @JsonProperty("passkey")
    PASSKEY,

    @JsonProperty("oob")
    OOB
}
