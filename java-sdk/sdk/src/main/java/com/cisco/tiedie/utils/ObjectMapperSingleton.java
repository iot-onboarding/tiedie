// Copyright (c) 2023, Cisco Systems, Inc. and/or its affiliates.
// All rights reserved.
// See LICENSE file in this distribution.
// SPDX-License-Identifier: Apache-2.0

package com.cisco.tiedie.utils;

import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.dataformat.cbor.databind.CBORMapper;


public class ObjectMapperSingleton {
    private static ObjectMapper objectMapper;
    private static CBORMapper cborMapper;

    private ObjectMapperSingleton() {}

    public static ObjectMapper getInstance() {
        if (objectMapper != null) {
            return objectMapper;
        }

        objectMapper = new ObjectMapper();
        objectMapper.setSerializationInclusion(JsonInclude.Include.NON_NULL);

        return objectMapper;
    }

    public static ObjectMapper getCborInstance() {
        cborMapper = new CBORMapper();
        cborMapper.setSerializationInclusion(JsonInclude.Include.NON_NULL);

        return cborMapper;
    }
}
