// Copyright (c) 2023, Cisco and/or its affiliates.
// All rights reserved.
// See license in distribution for details.

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
