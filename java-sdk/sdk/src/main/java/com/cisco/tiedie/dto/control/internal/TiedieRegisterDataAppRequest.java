// Copyright (c) 2023, Cisco Systems, Inc. and/or its affiliates.
// All rights reserved.
// See LICENSE file in this distribution.
// SPDX-License-Identifier: Apache-2.0

package com.cisco.tiedie.dto.control.internal;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.List;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class TiedieRegisterDataAppRequest {
    private String topic;
    private List<String> dataApps;

    public static TiedieRegisterDataAppRequest createRequest(String dataApp, String topic) {
        return new TiedieRegisterDataAppRequest(topic, List.of(dataApp));
    }
}
