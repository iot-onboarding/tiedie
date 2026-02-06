// Copyright (c) 2023, Cisco Systems, Inc. and/or its affiliates.
// All rights reserved.
// See LICENSE file in this distribution.
// SPDX-License-Identifier: Apache-2.0

package com.cisco.tiedie.dto.nipc;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class NipcResponse<T> {
    private NipcHttp http;
    private T body;
    private ProblemDetails error;

    public boolean isSuccess() {
        return error == null && (http == null || http.getStatusCode() < 400);
    }

    public boolean isError() {
        return !isSuccess();
    }
}
