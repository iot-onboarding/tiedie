// Copyright (c) 2023, Cisco and/or its affiliates.
// All rights reserved.
// See LICENSE file in this distribution.
// SPDX-License-Identifier: Apache-2.0

package com.cisco.tiedie.dto.control;

import lombok.Data;

import java.util.List;

@Data
public class DiscoverResponse {
    private List<DataParameter> dataParameters;
}
