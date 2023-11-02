// Copyright (c) 2023, Cisco and/or its affiliates.
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
import org.jetbrains.annotations.NotNull;

import java.io.IOException;
import java.util.*;
import java.util.concurrent.TimeUnit;

@SuppressWarnings("SameParameterValue")
abstract class AbstractHttpClient {

    private final String baseUrl;

    protected final OkHttpClient httpClient;

    private final ObjectMapper mapper = ObjectMapperSingleton.getInstance();

    private final MediaType mediaType;

    AbstractHttpClient(String baseUrl, MediaType mediaType, Authenticator authenticator) {
        this.baseUrl = baseUrl;
        this.mediaType = mediaType;

        var httpClientBuilder = OkHttpSingleton.getInstance()
                .newBuilder()
                .callTimeout(1, TimeUnit.MINUTES);

        httpClient = authenticator.setAuthOptions(httpClientBuilder)
                .build();
    }

    @NotNull
    private <V> TiedieResponse<V> getTiedieResponse(Class<V> returnClass, Response response) {
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
            return tiedieResponse;
        }
        return tiedieResponse;
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
            return getTiedieResponse(returnClass, response);
        }
    }

    <V> HttpResponse<V> get(String path, Class<V> returnClass) throws IOException {
        return get(path, null, returnClass);
    }

    <T, V> HttpResponse<V> get(String path, T body, Class<V> returnClass) throws IOException {
        List<String[]> queryParameters = getQueryParameters(body);
        HttpUrl.Builder urlBuilder
                = Objects.requireNonNull(HttpUrl.parse(baseUrl + path)).newBuilder();

        for (String[] queryParameter : queryParameters) {
            urlBuilder.addQueryParameter(queryParameter[0], queryParameter[1]);
        }
        Request request = new Request.Builder()
                .get()
                .url(urlBuilder.build().toString())
                .build();

        try (Response response = httpClient.newCall(request).execute()) {
            return mapResponse(response, returnClass);
        }
    }

    <V> TiedieResponse<V> getWithTiedieResponse(String path, Class<V> returnClass) throws IOException {
        return getWithTiedieResponse(path, null, returnClass);
    }

    <T, V> TiedieResponse<V> getWithTiedieResponse(String path, T body, Class<V> returnClass) throws IOException {
        List<String[]> queryParameters = getQueryParameters(body);
        HttpUrl.Builder urlBuilder
                = Objects.requireNonNull(HttpUrl.parse(baseUrl + path)).newBuilder();

        for (String[] queryParameter : queryParameters) {
            urlBuilder.addQueryParameter(queryParameter[0], queryParameter[1]);
        }
        Request request = new Request.Builder()
                .get()
                .url(urlBuilder.build().toString())
                .build();

        try (Response response = httpClient.newCall(request).execute()) {
            return getTiedieResponse(returnClass, response);
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

    <V> TiedieResponse<V> deleteWithTiedieResponse(String path, Class<V> returnClass) throws IOException {
        return deleteWithTiedieResponse(path, null, returnClass);
    }

    <T, V> TiedieResponse<V> deleteWithTiedieResponse(String path, T body, Class<V> returnClass) throws IOException {
        List<String[]> queryParameters = getQueryParameters(body);
        Request request = new Request.Builder()
                .delete()
                .url(baseUrl + path)
                .build();

        try (Response response = httpClient.newCall(request).execute()) {
            return getTiedieResponse(returnClass, response);
        }
    }

    protected <T> List<String[]> getQueryParameters(T body) {
        if (body == null) {
            return List.of();
        }
        var objectMap = mapper.convertValue(body, new TypeReference<Map<String, Object>>() {
        });

        List<String[]> queryParameters = new ArrayList<>();

        var stack = new ArrayList<Map.Entry<String, Object>>(objectMap.entrySet());

        while (!stack.isEmpty()) {
            var entry = stack.remove(stack.size() - 1);
            var key = entry.getKey();
            var value = entry.getValue();
            if (value instanceof Map) {
                for (var subEntry : ((Map<?, ?>) value).entrySet()) {
                    stack.add(Map.entry(key + "[" + subEntry.getKey() + "]", subEntry.getValue()));
                }
            } else if (value instanceof List) {
                for (var subValue : (List<?>) value) {
                    stack.add(Map.entry(key, subValue));
                }
            } else {
                queryParameters.add(new String[]{key, value.toString()});
            }
        }

        Collections.reverse(queryParameters);

        return queryParameters;
    }
}
