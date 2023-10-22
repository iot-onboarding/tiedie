// Copyright (c) 2023, Cisco and/or its affiliates.
// All rights reserved.
// See license in distribution for details.

package com.cisco.tiedie.dto.control;

import com.cisco.tiedie.dto.control.ble.BleAdvertisementFilter;
import com.cisco.tiedie.dto.control.ble.BleAdvertisementFilterType;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.EqualsAndHashCode;
import lombok.NoArgsConstructor;
import lombok.experimental.SuperBuilder;

import java.util.List;

@EqualsAndHashCode(callSuper = true)
@SuperBuilder
@Data
@NoArgsConstructor
@AllArgsConstructor
public class AdvertisementRegistrationOptions extends RegistrationOptions {
    private BleAdvertisementFilterType advertisementFilterType;
    private List<BleAdvertisementFilter> advertisementFilters;
}
