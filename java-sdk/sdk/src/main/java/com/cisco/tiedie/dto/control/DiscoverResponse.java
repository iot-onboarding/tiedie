// Copyright (c) 2023, Cisco and/or its affiliates.
// All rights reserved.
// See license in distribution for details.

package com.cisco.tiedie.dto.control;

import lombok.Data;

import java.util.List;

@Data
public class DiscoverResponse {
    private List<DataParameter> dataParameters;
}
