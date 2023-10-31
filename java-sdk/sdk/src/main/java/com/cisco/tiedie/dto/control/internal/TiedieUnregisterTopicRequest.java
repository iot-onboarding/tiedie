// Copyright (c) 2023, Cisco and/or its affiliates.
// All rights reserved.
// See LICENSE file in this distribution.
// SPDX-License-Identifier: Apache-2.0

package com.cisco.tiedie.dto.control.internal;

import java.util.List;

import lombok.Data;
import lombok.EqualsAndHashCode;


@Data
@EqualsAndHashCode(callSuper = true)
public class TiedieUnregisterTopicRequest extends TiedieBasicRequest {
    private String topic;
    private List<String> ids;

    public static TiedieUnregisterTopicRequest createRequest(String topic, List<String> uuids, String controlAppId) {
        var tiedieRequest = new TiedieUnregisterTopicRequest();

        tiedieRequest.setControlApp(controlAppId);
        tiedieRequest.setIds(uuids);
        tiedieRequest.setTopic(topic);

        return tiedieRequest;
    }
}
