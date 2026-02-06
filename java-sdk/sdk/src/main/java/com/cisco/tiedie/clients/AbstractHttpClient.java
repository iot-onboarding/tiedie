// Copyright (c) 2023, Cisco Systems, Inc. and/or its affiliates.
// All rights reserved.
// See LICENSE file in this distribution.
// SPDX-License-Identifier: Apache-2.0

package com.cisco.tiedie.clients;

import com.cisco.tiedie.auth.Authenticator;
import com.cisco.tiedie.dto.HttpResponse;
import com.cisco.tiedie.dto.nipc.NipcHttp;
import com.cisco.tiedie.dto.nipc.NipcProblemType;
import com.cisco.tiedie.dto.nipc.NipcResponse;
import com.cisco.tiedie.dto.nipc.ProblemDetails;
import com.cisco.tiedie.utils.ObjectMapperSingleton;
import com.cisco.tiedie.utils.OkHttpSingleton;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import okhttp3.*;
import org.jetbrains.annotations.NotNull;

import java.io.IOException;
import java.util.*;
import java.util.concurrent.atomic.AtomicLong;
import java.util.concurrent.TimeUnit;
import java.util.logging.Logger;

@SuppressWarnings("SameParameterValue")
abstract class AbstractHttpClient {

    private static final String DEFAULT_NIPC_CONTENT_TYPE = "application/nipc+json";
    private static final Logger LOGGER = Logger.getLogger(AbstractHttpClient.class.getName());
    private static final AtomicLong REQUEST_COUNTER = new AtomicLong(0);

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
                .addNetworkInterceptor(chain -> {
                    Request request = chain.request();
                    long requestId = REQUEST_COUNTER.incrementAndGet();

                    LOGGER.info(() -> String.format(
                            "HTTP[%d] Request %s %s headers=%s",
                            requestId,
                            request.method(),
                            request.url(),
                            mapHeaders(request.headers())
                    ));

                    try {
                        Response response = chain.proceed(request);
                        LOGGER.info(() -> String.format(
                                "HTTP[%d] Response %d %s headers=%s",
                                requestId,
                                response.code(),
                                response.message(),
                                mapHeaders(response.headers())
                        ));
                        return response;
                    } catch (IOException e) {
                        LOGGER.warning(String.format(
                                "HTTP[%d] Request failed: %s %s error=%s",
                                requestId,
                                request.method(),
                                request.url(),
                                e.getMessage()
                        ));
                        throw e;
                    }
                })
                .build();
    }

    private RequestBody createRequestBody(Object body, MediaType requestMediaType) throws JsonProcessingException {
        if (body == null) {
            return RequestBody.create("", requestMediaType);
        }

        return RequestBody.create(mapper.writeValueAsString(body), requestMediaType);
    }

    private Map<String, String> mapHeaders(Headers headers) {
        Map<String, String> mappedHeaders = new LinkedHashMap<>();

        for (String name : headers.names()) {
            var values = headers.values(name);
            mappedHeaders.put(name, String.join(",", values));
        }

        return mappedHeaders;
    }

    private ProblemDetails fallbackProblem(Response response, String body, Exception parseException) {
        ProblemDetails problemDetails = new ProblemDetails();
        problemDetails.setType(NipcProblemType.ABOUT_BLANK);
        problemDetails.setStatus(response.code());
        problemDetails.setTitle(response.message());

        String detail = (body == null || body.isEmpty()) ? response.message() : body;
        if (parseException != null) {
            detail = "Failed to parse error response: " + parseException.getMessage();
        }
        problemDetails.setDetail(detail);

        return problemDetails;
    }

    private ProblemDetails parseProblemDetails(Response response, String body) {
        String contentType = Objects.requireNonNull(response.header("content-type", "")).toLowerCase(Locale.ROOT);

        if (!body.isEmpty() && contentType.contains("application/problem+json")) {
            try {
                return mapper.readValue(body, ProblemDetails.class);
            } catch (IOException e) {
                return fallbackProblem(response, body, e);
            }
        }

        return fallbackProblem(response, body, null);
    }

    @NotNull
    private <V> NipcResponse<V> mapNipcResponse(
            Response response,
            Class<V> returnClass,
            TypeReference<V> returnTypeReference
    ) {
        NipcResponse<V> nipcResponse = new NipcResponse<>();

        NipcHttp http = new NipcHttp(
                response.code(),
                response.message(),
                mapHeaders(response.headers())
        );
        nipcResponse.setHttp(http);

        ResponseBody responseBody = response.body();
        String body = "";

        if (responseBody != null) {
            try {
                body = responseBody.string();
            } catch (IOException e) {
                ProblemDetails parsingError = new ProblemDetails(
                        NipcProblemType.ABOUT_BLANK,
                        500,
                        "Response Parsing Error",
                        "Failed to read response body: " + e.getMessage()
                );
                nipcResponse.setError(parsingError);
                return nipcResponse;
            }
        }

        if (response.code() >= 400) {
            nipcResponse.setError(parseProblemDetails(response, body));
            return nipcResponse;
        }

        if (returnClass == null && returnTypeReference == null) {
            return nipcResponse;
        }

        if (returnClass == Void.class || body.isEmpty()) {
            return nipcResponse;
        }

        try {
            if (returnClass != null) {
                nipcResponse.setBody(mapper.readValue(body, returnClass));
            } else {
                nipcResponse.setBody(mapper.readValue(body, returnTypeReference));
            }
        } catch (IOException e) {
            ProblemDetails parsingError = new ProblemDetails(
                    NipcProblemType.ABOUT_BLANK,
                    500,
                    "Response Parsing Error",
                    "Failed to parse success response: " + e.getMessage()
            );
            nipcResponse.setError(parsingError);
        }

        return nipcResponse;
    }

    private <V> HttpResponse<V> mapResponse(Response response, Class<V> returnClass) {
        HttpResponse<V> httpResponse = new HttpResponse<>();
        httpResponse.setStatusCode(response.code());
        httpResponse.setMessage(response.message());

        if (returnClass == null || returnClass == Void.class) {
            return httpResponse;
        }

        ResponseBody responseBody = response.body();

        if (responseBody == null) {
            return httpResponse;
        }

        try {
            httpResponse.setBody(mapper.readValue(responseBody.string(), returnClass));
        } catch (IOException ignored) {
            // Keep body unset when parsing fails.
        }

        return httpResponse;
    }

    <T, V> HttpResponse<V> post(String path, T body, Class<V> returnClass) throws IOException {
        RequestBody requestBody = createRequestBody(body, mediaType);

        Request request = new Request.Builder()
                .url(baseUrl + path)
                .post(requestBody)
                .build();

        try (Response response = httpClient.newCall(request).execute()) {
            return mapResponse(response, returnClass);
        }
    }

    <T, V> HttpResponse<V> put(String path, T body, Class<V> returnClass) throws IOException {
        RequestBody requestBody = createRequestBody(body, mediaType);

        Request request = new Request.Builder()
                .url(baseUrl + path)
                .put(requestBody)
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

    <T, V> NipcResponse<V> postWithNipcResponse(String path, T body, Class<V> returnClass) throws IOException {
        return postWithNipcResponse(path, body, returnClass, MediaType.parse(DEFAULT_NIPC_CONTENT_TYPE));
    }

    <T, V> NipcResponse<V> postWithNipcResponse(
            String path,
            T body,
            Class<V> returnClass,
            MediaType contentType
    ) throws IOException {
        RequestBody requestBody = createRequestBody(body, contentType);

        Request request = new Request.Builder()
                .url(baseUrl + path)
                .post(requestBody)
                .header("Content-Type", contentType.toString())
                .build();

        try (Response response = httpClient.newCall(request).execute()) {
            return mapNipcResponse(response, returnClass, null);
        }
    }

    <T, V> NipcResponse<V> postWithNipcResponse(
            String path,
            T body,
            TypeReference<V> returnTypeReference,
            MediaType contentType
    ) throws IOException {
        RequestBody requestBody = createRequestBody(body, contentType);

        Request request = new Request.Builder()
                .url(baseUrl + path)
                .post(requestBody)
                .header("Content-Type", contentType.toString())
                .build();

        try (Response response = httpClient.newCall(request).execute()) {
            return mapNipcResponse(response, null, returnTypeReference);
        }
    }

    <V> NipcResponse<V> getWithNipcResponse(String path, Class<V> returnClass) throws IOException {
        Request request = new Request.Builder()
                .get()
                .url(baseUrl + path)
                .build();

        try (Response response = httpClient.newCall(request).execute()) {
            return mapNipcResponse(response, returnClass, null);
        }
    }

    <V> NipcResponse<V> getWithNipcResponse(String path, TypeReference<V> returnTypeReference) throws IOException {
        Request request = new Request.Builder()
                .get()
                .url(baseUrl + path)
                .build();

        try (Response response = httpClient.newCall(request).execute()) {
            return mapNipcResponse(response, null, returnTypeReference);
        }
    }

    <T, V> NipcResponse<V> putWithNipcResponse(String path, T body, Class<V> returnClass) throws IOException {
        return putWithNipcResponse(path, body, returnClass, MediaType.parse(DEFAULT_NIPC_CONTENT_TYPE));
    }

    <T, V> NipcResponse<V> putWithNipcResponse(String path, T body, TypeReference<V> returnTypeReference) throws IOException {
        return putWithNipcResponse(path, body, returnTypeReference, MediaType.parse(DEFAULT_NIPC_CONTENT_TYPE));
    }

    <T, V> NipcResponse<V> putWithNipcResponse(
            String path,
            T body,
            Class<V> returnClass,
            MediaType contentType
    ) throws IOException {
        RequestBody requestBody = createRequestBody(body, contentType);

        Request request = new Request.Builder()
                .url(baseUrl + path)
                .put(requestBody)
                .header("Content-Type", contentType.toString())
                .build();

        try (Response response = httpClient.newCall(request).execute()) {
            return mapNipcResponse(response, returnClass, null);
        }
    }

    <T, V> NipcResponse<V> putWithNipcResponse(
            String path,
            T body,
            TypeReference<V> returnTypeReference,
            MediaType contentType
    ) throws IOException {
        RequestBody requestBody = createRequestBody(body, contentType);

        Request request = new Request.Builder()
                .url(baseUrl + path)
                .put(requestBody)
                .header("Content-Type", contentType.toString())
                .build();

        try (Response response = httpClient.newCall(request).execute()) {
            return mapNipcResponse(response, null, returnTypeReference);
        }
    }

    <V> NipcResponse<V> deleteWithNipcResponse(String path, Class<V> returnClass) throws IOException {
        Request request = new Request.Builder()
                .delete()
                .url(baseUrl + path)
                .build();

        try (Response response = httpClient.newCall(request).execute()) {
            return mapNipcResponse(response, returnClass, null);
        }
    }
}
