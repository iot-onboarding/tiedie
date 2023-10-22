// Copyright (c) 2023, Cisco and/or its affiliates.
// All rights reserved.
// See license in distribution for details.

package com.cisco.tiedie.dto.control.internal;

import java.util.List;

import lombok.Data;
import lombok.EqualsAndHashCode;


@Data
@EqualsAndHashCode(callSuper = true)
public class TiedieUnregisterTopicRequest extends TiedieBasicRequest {
    private String topic;
    private List<String> uuids;

    public static TiedieUnregisterTopicRequest createRequest(String topic, List<String> uuids, String controlAppId) {
        var tiedieRequest = new TiedieUnregisterTopicRequest();

        tiedieRequest.setControlApp(controlAppId);
        tiedieRequest.setUuids(uuids);
        tiedieRequest.setTopic(topic);

        return tiedieRequest;
    }
}
