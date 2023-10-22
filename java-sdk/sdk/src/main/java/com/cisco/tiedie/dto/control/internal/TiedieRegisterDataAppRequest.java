// Copyright (c) 2023, Cisco and/or its affiliates.
// All rights reserved.
// See license in distribution for details.

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
    private String controlApp;

    public static TiedieRegisterDataAppRequest createRequest(String dataApp, String topic, String controlApp) {
        return new TiedieRegisterDataAppRequest(topic, List.of(dataApp), controlApp);
    }
}
