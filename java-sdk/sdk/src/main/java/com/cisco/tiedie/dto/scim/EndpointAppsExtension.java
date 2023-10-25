// Copyright (c) 2023, Cisco and/or its affiliates.
// All rights reserved.
// See license in distribution for details.

package com.cisco.tiedie.dto.scim;

import java.util.List;
import lombok.Builder;
import lombok.Data;
import lombok.extern.jackson.Jacksonized;

@Data
@Jacksonized
@Builder(builderClassName = "Builder")
public class EndpointAppsExtension {
    private String onboardingUrl;
    private List<String> deviceControlUrl;
    private List<String> dataReceiverUrl;
}
