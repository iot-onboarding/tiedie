// Copyright (c) 2023, Cisco Systems, Inc. and/or its affiliates.
// All rights reserved.
// See LICENSE file in this distribution.
// SPDX-License-Identifier: Apache-2.0

package com.cisco.tiedie.clients;

import com.cisco.tiedie.auth.Authenticator;
import com.cisco.tiedie.dto.control.DataParameter;
import com.cisco.tiedie.dto.control.DataResponse;
import com.cisco.tiedie.dto.control.ble.BleConnectRequest;
import com.cisco.tiedie.dto.control.ble.BleDiscoverResponse;
import com.cisco.tiedie.dto.nipc.*;
import com.cisco.tiedie.dto.scim.Device;
import com.fasterxml.jackson.core.type.TypeReference;
import okhttp3.MediaType;

import java.io.IOException;
import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.Map;

/**
 * This class is used to communicate with the TieDie NIPC APIs.
 */
public class ControlClient extends AbstractHttpClient {

    private static final MediaType NIPC_MEDIA_TYPE = MediaType.parse("application/nipc+json");
    private static final MediaType SDF_MEDIA_TYPE = MediaType.parse("application/sdf+json");

    /**
     * Create a {@link ControlClient} object.
     *
     * @param baseUrl       The TieDie controller base URL.
     * @param authenticator {@link Authenticator} object that describes the authentication mechanism used.
     */
    public ControlClient(String baseUrl, Authenticator authenticator) {
        super(baseUrl, NIPC_MEDIA_TYPE, authenticator);
    }

    private static String encode(String value) {
        return URLEncoder.encode(value, StandardCharsets.UTF_8).replace("+", "%20");
    }

    private static void validateDevice(Device device) {
        if (device == null || device.getId() == null || device.getId().isBlank()) {
            throw new IllegalArgumentException("Device ID is required");
        }
    }

    private NipcResponse<List<DataParameter>> mapDiscoveryResponse(
            String deviceId,
            NipcResponse<BleDiscoverResponse> response
    ) {
        NipcResponse<List<DataParameter>> mapped = new NipcResponse<>();
        mapped.setHttp(response.getHttp());
        mapped.setError(response.getError());

        if (response.isSuccess() && response.getBody() != null) {
            mapped.setBody(response.getBody().toParameterList(deviceId));
        }

        return mapped;
    }

    @SuppressWarnings("SameParameterValue")
    private static String findHeader(Map<String, String> headers, String key) {
        if (headers == null) {
            return null;
        }

        for (Map.Entry<String, String> header : headers.entrySet()) {
            if (header.getKey().equalsIgnoreCase(key)) {
                return header.getValue();
            }
        }

        return null;
    }

    private static Map<String, Object> connectRequestBody(
            BleConnectRequest request,
            int retries,
            boolean retryMultipleAps
    ) {
        BleConnectRequest safeRequest = request == null ? new BleConnectRequest() : request;

        return Map.of(
                "sdfProtocolMap", Map.of("ble", safeRequest),
                "retries", retries,
                "retryMultipleAPs", retryMultipleAps
        );
    }

    private static Map<String, Object> propertyProtocolMap(String serviceId, String characteristicId) {
        return Map.of(
                "sdfProtocolMap",
                Map.of(
                        "ble",
                        Map.of(
                                "serviceID", serviceId,
                                "characteristicID", characteristicId
                        )
                )
        );
    }

    public NipcResponse<List<DataParameter>> connect(Device device) throws IOException {
        return connect(device, new BleConnectRequest(), 3, true);
    }

    public NipcResponse<List<DataParameter>> connect(Device device, BleConnectRequest request) throws IOException {
        return connect(device, request, 3, true);
    }

    public NipcResponse<List<DataParameter>> connect(
            Device device,
            BleConnectRequest request,
            int retries,
            boolean retryMultipleAps
    ) throws IOException {
        validateDevice(device);

        Map<String, Object> tiedieRequest = connectRequestBody(request, retries, retryMultipleAps);

        NipcResponse<BleDiscoverResponse> response = postWithNipcResponse(
                "/devices/" + device.getId() + "/connections",
                tiedieRequest,
                BleDiscoverResponse.class
        );

        return mapDiscoveryResponse(device.getId(), response);
    }

    public NipcResponse<TiedieDeviceResponse> disconnect(Device device) throws IOException {
        validateDevice(device);

        return deleteWithNipcResponse(
                "/devices/" + device.getId() + "/connections",
                TiedieDeviceResponse.class
        );
    }

    public NipcResponse<List<DataParameter>> getConnection(Device device) throws IOException {
        validateDevice(device);

        NipcResponse<BleDiscoverResponse> response = getWithNipcResponse(
                "/devices/" + device.getId() + "/connections",
                BleDiscoverResponse.class
        );

        return mapDiscoveryResponse(device.getId(), response);
    }

    public NipcResponse<List<DataParameter>> discover(Device device) throws IOException {
        return discover(device, new BleConnectRequest(), 3, true);
    }

    public NipcResponse<List<DataParameter>> discover(Device device, BleConnectRequest request) throws IOException {
        return discover(device, request, 3, true);
    }

    public NipcResponse<List<DataParameter>> discover(
            Device device,
            BleConnectRequest request,
            int retries,
            boolean retryMultipleAps
    ) throws IOException {
        validateDevice(device);

        Map<String, Object> tiedieRequest = connectRequestBody(request, retries, retryMultipleAps);

        NipcResponse<BleDiscoverResponse> response = putWithNipcResponse(
                "/devices/" + device.getId() + "/connections",
                tiedieRequest,
                BleDiscoverResponse.class
        );

        return mapDiscoveryResponse(device.getId(), response);
    }

    public NipcResponse<DataResponse> read(Device device, String serviceId, String characteristicId) throws IOException {
        validateDevice(device);

        Map<String, Object> request = propertyProtocolMap(serviceId, characteristicId);
        String endpoint = "/extensions/" + device.getId() + "/properties/read";

        return postWithNipcResponse(endpoint, request, DataResponse.class);
    }

    public NipcResponse<DataResponse> write(
            Device device,
            String serviceId,
            String characteristicId,
            String value
    ) throws IOException {
        validateDevice(device);

        Map<String, Object> request = Map.of(
                "value", value,
                "sdfProtocolMap",
                Map.of(
                        "ble",
                        Map.of(
                                "serviceID", serviceId,
                                "characteristicID", characteristicId
                        )
                )
        );
        String endpoint = "/extensions/" + device.getId() + "/properties/write";

        return postWithNipcResponse(endpoint, request, DataResponse.class);
    }

    public NipcResponse<List<PropertyReadResult>> readProperty(String deviceId, String sdfName) throws IOException {
        String endpoint = "/devices/" + deviceId + "/properties?propertyName=" + encode(sdfName);

        return getWithNipcResponse(endpoint, new TypeReference<>() {});
    }

    public NipcResponse<List<PropertyWriteResult>> writeProperty(
            String deviceId,
            String sdfName,
            String value
    ) throws IOException {
        String endpoint = "/devices/" + deviceId + "/properties";

        return putWithNipcResponse(
                endpoint,
                List.of(Map.of("property", sdfName, "value", value)),
                new TypeReference<>() {}
        );
    }

    public NipcResponse<List<ModelRegistrationResponse>> registerSdfModel(SdfModel model) throws IOException {
        return postWithNipcResponse(
                "/registrations/models",
                model,
                new TypeReference<>() {},
                SDF_MEDIA_TYPE
        );
    }

    public NipcResponse<ModelRegistrationResponse> updateSdfModel(String sdfName, SdfModel model) throws IOException {
        return putWithNipcResponse(
                "/registrations/models?sdfName=" + encode(sdfName),
                model,
                ModelRegistrationResponse.class,
                SDF_MEDIA_TYPE
        );
    }

    public NipcResponse<List<ModelRegistrationResponse>> getSdfModels() throws IOException {
        return getWithNipcResponse(
                "/registrations/models",
                new TypeReference<>() {}
        );
    }

    public NipcResponse<SdfModel> getSdfModel(String sdfName) throws IOException {
        return getWithNipcResponse(
                "/registrations/models?sdfName=" + encode(sdfName),
                SdfModel.class
        );
    }

    public NipcResponse<ModelRegistrationResponse> unregisterSdfModel(String sdfName) throws IOException {
        return deleteWithNipcResponse(
                "/registrations/models?sdfName=" + encode(sdfName),
                ModelRegistrationResponse.class
        );
    }

    public NipcResponse<DataAppRegistration> getDataApp(String dataAppId) throws IOException {
        return getWithNipcResponse(
                "/registrations/data-apps?dataAppId=" + encode(dataAppId),
                DataAppRegistration.class
        );
    }

    public NipcResponse<DataAppRegistration> createDataApp(
            String dataAppId,
            DataAppRegistration dataApp
    ) throws IOException {
        return postWithNipcResponse(
                "/registrations/data-apps?dataAppId=" + encode(dataAppId),
                dataApp,
                DataAppRegistration.class
        );
    }

    public NipcResponse<DataAppRegistration> updateDataApp(
            String dataAppId,
            DataAppRegistration dataApp
    ) throws IOException {
        return putWithNipcResponse(
                "/registrations/data-apps?dataAppId=" + encode(dataAppId),
                dataApp,
                DataAppRegistration.class
        );
    }

    public NipcResponse<DataAppRegistration> deleteDataApp(String dataAppId) throws IOException {
        return deleteWithNipcResponse(
                "/registrations/data-apps?dataAppId=" + encode(dataAppId),
                DataAppRegistration.class
        );
    }

    public NipcResponse<String> enableEvent(String deviceId, String eventName) throws IOException {
        NipcResponse<Void> response = postWithNipcResponse(
                "/devices/" + deviceId + "/events?eventName=" + encode(eventName),
                null,
                Void.class
        );

        NipcResponse<String> mapped = new NipcResponse<>();
        mapped.setHttp(response.getHttp());
        mapped.setError(response.getError());

        if (!response.isSuccess() || response.getHttp() == null) {
            return mapped;
        }

        String location = findHeader(response.getHttp().getHeaders(), "Location");
        if (location == null) {
            return mapped;
        }

        int index = location.indexOf("instanceId=");
        if (index < 0) {
            return mapped;
        }

        String instanceId = location.substring(index + "instanceId=".length());
        int ampersand = instanceId.indexOf('&');
        if (ampersand >= 0) {
            instanceId = instanceId.substring(0, ampersand);
        }

        mapped.setBody(instanceId);

        return mapped;
    }

    public NipcResponse<Void> disableEvent(String deviceId, String instanceId) throws IOException {
        return deleteWithNipcResponse(
                "/devices/" + deviceId + "/events?instanceId=" + encode(instanceId),
                Void.class
        );
    }

    public NipcResponse<List<TiedieEventResponse>> getEvent(String deviceId, String instanceId) throws IOException {
        return getWithNipcResponse(
                "/devices/" + deviceId + "/events?instanceId=" + encode(instanceId),
                new TypeReference<>() {}
        );
    }

    public NipcResponse<List<TiedieEventResponse>> getAllEvents(String deviceId) throws IOException {
        return getWithNipcResponse(
                "/devices/" + deviceId + "/events",
                new TypeReference<>() {}
        );
    }
}
