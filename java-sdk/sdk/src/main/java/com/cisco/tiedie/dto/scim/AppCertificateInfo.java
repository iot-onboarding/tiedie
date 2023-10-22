// Copyright (c) 2023, Cisco and/or its affiliates.
// All rights reserved.
// See license in distribution for details.

package com.cisco.tiedie.dto.scim;


import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.extern.jackson.Jacksonized;

import java.util.List;

@Data
@AllArgsConstructor
@NoArgsConstructor
@Jacksonized
@Builder(builderClassName = "Builder")
public class AppCertificateInfo {
    private String rootCN;
    private String subjectName;
    private List<String> subjectAlternativeName;
}
