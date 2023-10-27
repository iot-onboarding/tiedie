// Copyright (c) 2023, Cisco and/or its affiliates.
// All rights reserved.
// See LICENSE file in this distribution.
// SPDX-License-Identifier: Apache-2.0

package com.cisco.tiedie.utils;

import okhttp3.OkHttpClient;

public class OkHttpSingleton {
    private static OkHttpClient client;

    private OkHttpSingleton() {}

    public static OkHttpClient getInstance() {
        if (client != null) {
            return client;
        }

        client = new OkHttpClient();
        return client;
    }
}
