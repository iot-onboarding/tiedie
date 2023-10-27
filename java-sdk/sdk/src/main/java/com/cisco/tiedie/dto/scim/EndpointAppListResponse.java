// Copyright (c) 2023, Cisco and/or its affiliates.
// All rights reserved.
// See LICENSE file in this distribution.
// SPDX-License-Identifier: Apache-2.0

package com.cisco.tiedie.dto.scim;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Data;

import java.util.List;

/**
 *
 */
@Data
@JsonIgnoreProperties(ignoreUnknown = true)
public class EndpointAppListResponse {
    private Integer totalResults;
    private Integer startIndex;
    private Integer itemsPerPage;

    @JsonProperty("Resources")
    private List<EndpointApp> resources;
}
