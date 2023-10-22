// Copyright (c) 2023, Cisco and/or its affiliates.
// All rights reserved.
// See license in distribution for details.

package com.cisco.tiedie.dto.control;


import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.EqualsAndHashCode;
import lombok.NoArgsConstructor;
import lombok.experimental.SuperBuilder;

@EqualsAndHashCode(callSuper = true)
@SuperBuilder
@Data
@NoArgsConstructor
@AllArgsConstructor
public class DataRegistrationOptions extends RegistrationOptions {
    private DataParameter dataParameter;
}
