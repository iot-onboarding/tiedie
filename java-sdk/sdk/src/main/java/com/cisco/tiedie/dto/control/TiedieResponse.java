// Copyright (c) 2023, Cisco Systems, Inc. and/or its affiliates.
// All rights reserved.
// See LICENSE file in this distribution.
// SPDX-License-Identifier: Apache-2.0

package com.cisco.tiedie.dto.control;

import com.fasterxml.jackson.annotation.JsonAnySetter;
import com.fasterxml.jackson.annotation.JsonIgnore;
import com.fasterxml.jackson.databind.JsonNode;
import lombok.Data;

import java.util.HashMap;
import java.util.Map;

@Data
public class TiedieResponse<T> {
    private TiedieStatus status;
    private String reason;
    private int errorCode;
    private String requestID;

    @JsonIgnore
    private T body;

    @JsonIgnore
    private int httpStatusCode;

    @JsonIgnore
    private String httpMessage;

    @JsonIgnore
    private Map<String, JsonNode> map = new HashMap<>();

    @JsonAnySetter
    public void unpackRemaining(String key, JsonNode value) {
        map.put(key, value);
    }
}
