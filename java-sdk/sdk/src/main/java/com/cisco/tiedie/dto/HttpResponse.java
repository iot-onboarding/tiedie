// Copyright (c) 2023, Cisco and/or its affiliates.
// All rights reserved.
// See LICENSE file in this distribution.
// SPDX-License-Identifier: Apache-2.0

package com.cisco.tiedie.dto;

import lombok.Data;

/**
 * Wrapper for the HTTP response.
 *
 * @param <T> Type of the JSON body.
 */
@Data
public class HttpResponse<T> {
    /**
     * HTTP status
     */
    private int statusCode;

    /**
     * HTTP status message
     */
    private String message;

    /**
     * HTTP body JSON serialized to the generic class.
     */
    private T body;
}
