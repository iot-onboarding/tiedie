// Copyright (c) 2023, Cisco Systems, Inc. and/or its affiliates.
// All rights reserved.
// See LICENSE file in this distribution.
// SPDX-License-Identifier: Apache-2.0

package com.cisco.tiedie.clients;

import com.cisco.tiedie.auth.Authenticator;
import com.cisco.tiedie.dto.HttpResponse;
import com.cisco.tiedie.dto.control.TiedieResponse;
import com.cisco.tiedie.dto.control.TiedieStatus;
import com.cisco.tiedie.utils.ObjectMapperSingleton;
import com.cisco.tiedie.utils.OkHttpSingleton;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import okhttp3.*;

import java.io.IOException;
import java.util.concurrent.TimeUnit;

@SuppressWarnings("SameParameterValue")
abstract class AbstractHttpClient {

    private final String baseUrl;

    protected final OkHttpClient httpClient;

    private final ObjectMapper mapper = ObjectMapperSingleton.getInstance();

    private final MediaType mediaType;

    protected Authenticator authenticator;

    AbstractHttpClient(String baseUrl, MediaType mediaType, Authenticator authenticator) {
        this.baseUrl = baseUrl;
        this.mediaType = mediaType;
        this.authenticator = authenticator;

        var httpClientBuilder = OkHttpSingleton.getInstance()
                .newBuilder()
                .callTimeout(1, TimeUnit.MINUTES);

        httpClient = authenticator.setAuthOptions(httpClientBuilder)
                .build();
    }

    <T, V> TiedieResponse<V> postWithTiedieResponse(String path, T body, Class<V> returnClass) throws IOException {
        RequestBody requestBody = RequestBody.create(
                mapper.writeValueAsString(body),
                mediaType
        );

        Request request = new Request.Builder()
                .url(baseUrl + path)
                .post(requestBody)
                .build();

        try (Response response = httpClient.newCall(request).execute()) {
            ResponseBody responseBody = response.body();
            TiedieResponse<V> tiedieResponse = new TiedieResponse<>();
            tiedieResponse.setStatus(TiedieStatus.FAILURE);
            tiedieResponse.setHttpStatusCode(response.code());
            tiedieResponse.setHttpMessage(response.message());

            if (responseBody == null) {
                return tiedieResponse;
            }

            try {
                tiedieResponse = mapper.readValue(responseBody.string(), new TypeReference<>() {
                });

                tiedieResponse.setHttpStatusCode(response.code());
                tiedieResponse.setHttpMessage(response.message());
                tiedieResponse.setBody(mapper.convertValue(tiedieResponse.getMap(), returnClass));
            } catch (IOException e) {
                e.printStackTrace();
                return tiedieResponse;
            }
            return tiedieResponse;
        }
    }

    private <V> HttpResponse<V> mapResponse(Response response, Class<V> returnClass) {
        HttpResponse<V> httpResponse = new HttpResponse<>();
        httpResponse.setStatusCode(response.code());
        httpResponse.setMessage(response.message());

        ResponseBody responseBody = response.body();

        if (responseBody == null) {
            return httpResponse;
        }

        try {
            httpResponse.setBody(mapper.readValue(responseBody.string(), returnClass));
        } catch (IOException e) {
            return httpResponse;
        }
        return httpResponse;
    }

    <T, V> HttpResponse<V> post(String path, T body, Class<V> returnClass) throws IOException {
        RequestBody requestBody = RequestBody.create(
                mapper.writeValueAsString(body),
                mediaType
        );

        Request request = new Request.Builder()
                .url(baseUrl + path)
                .post(requestBody)
                .build();

        try (Response response = httpClient.newCall(request).execute()) {
            return mapResponse(response, returnClass);
        }
    }

    <V> HttpResponse<V> get(String path, Class<V> returnClass) throws IOException {
        Request request = new Request.Builder()
                .get()
                .url(baseUrl + path)
                .build();

        try (Response response = httpClient.newCall(request).execute()) {
            return mapResponse(response, returnClass);
        }
    }

    <V> HttpResponse<V> delete(String path, Class<V> returnClass) throws IOException {
        Request request = new Request.Builder()
                .delete()
                .url(baseUrl + path)
                .build();

        try (Response response = httpClient.newCall(request).execute()) {
            return mapResponse(response, returnClass);
        }
    }
}
