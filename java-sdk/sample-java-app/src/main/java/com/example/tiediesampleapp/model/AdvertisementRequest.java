// Copyright (c) 2023, Cisco and/or its affiliates.
// All rights reserved.
// See LICENSE file in this distribution.
// SPDX-License-Identifier: Apache-2.0

package com.example.tiediesampleapp.model;

import java.util.List;
import com.cisco.tiedie.dto.control.ble.BleAdvertisementFilter;
import com.cisco.tiedie.dto.control.ble.BleAdvertisementFilterType;

import lombok.Data;

@Data
public class AdvertisementRequest {
    private String topic;
    private BleAdvertisementFilterType filterType;
    private List<BleAdvertisementFilter> filters;
}
