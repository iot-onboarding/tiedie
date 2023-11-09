// Copyright (c) 2023, Cisco Systems, Inc. and/or its affiliates.
// All rights reserved.
// See LICENSE file in this distribution.
// SPDX-License-Identifier: Apache-2.0

package com.cisco.tiedie.dto.control;

import java.util.List;

import com.cisco.tiedie.dto.scim.Device;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.experimental.SuperBuilder;


@SuperBuilder
@Data
@NoArgsConstructor
@AllArgsConstructor
public abstract class RegistrationOptions {
    private Device device;
    private DataFormat dataFormat;
    private List<String> dataAppIds;
}
