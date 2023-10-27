// Copyright (c) 2023, Cisco and/or its affiliates.
// All rights reserved.
// See LICENSE file in this distribution.
// SPDX-License-Identifier: Apache-2.0

package com.cisco.tiedie.clients;

import com.cisco.tiedie.auth.Authenticator;
import com.cisco.tiedie.dto.HttpResponse;
import com.cisco.tiedie.dto.scim.Device;
import com.cisco.tiedie.dto.scim.EndpointApp;
import com.cisco.tiedie.dto.scim.DeviceListResponse;
import com.cisco.tiedie.dto.scim.EndpointAppListResponse;
import okhttp3.MediaType;

import java.io.IOException;
import java.util.List;

/**
 * This class is used to communicate with the TieDie onboarding SCIM APIs.
 * Create an Onboarding API client as follows:
 * <pre>
 * {@code
 * InputStream caInputStream = new FileInputStream("ca.pem");
 * Authenticator authenticator = ApiKeyAuthenticator.create(caInputStream, "app_id", "api_key");
 *
 * OnboardingClient onboardingClient = new OnboardingClient("https://<host>/scim/v2", authenticator);
 * }
 * </pre>
 * <p>
 * The above example uses an {@link com.cisco.tiedie.auth.ApiKeyAuthenticator}.
 *
 * @see Authenticator
 */
public class OnboardingClient extends AbstractHttpClient {

    /**
     * Create a {@link OnboardingClient} object.
     *
     * @param baseUrl       The TieDie controller base URL.
     * @param authenticator {@link Authenticator} object that describes the authentication mechanism used.
     */
    public OnboardingClient(String baseUrl, Authenticator authenticator) {
        super(baseUrl, MediaType.parse("application/scim+json"), authenticator);
    }

    /**
     * Onboard a new device on the controller.
     *
     * @param device {@link Device} object.
     * @return Updated device object with a valid ID (See {@link Device#getId()}).
     * @throws IOException if the request could not be executed due to cancellation, a connectivity problem or timeout.
     */
    public HttpResponse<Device> createDevice(Device device) throws IOException {
        return post("/Devices", device, Device.class);
    }

    /**
     * Get the Device object using its unique ID.
     *
     * @param id Unique ID of the device
     * @return Device object from the backend.
     * @throws IOException if the request could not be executed due to cancellation, a connectivity problem or timeout.
     */
    public HttpResponse<Device> getDevice(String id) throws IOException {
        return get("/Devices/" + id, Device.class);
    }

    /**
     * Get a list of Device objects.
     *
     * @return Device objects from the backend.
     * @throws IOException if the request could not be executed due to cancellation, a connectivity problem or timeout.
     */
    public HttpResponse<List<Device>> getDevices() throws IOException {
        HttpResponse<DeviceListResponse> httpResponse = get("/Devices", DeviceListResponse.class);

        HttpResponse<List<Device>> newResponse = new HttpResponse<>();
        newResponse.setStatusCode(httpResponse.getStatusCode());
        newResponse.setMessage(httpResponse.getMessage());
        newResponse.setBody(httpResponse.getBody().getResources());

        return newResponse;
    }

    /**
     * Un-onboard a device on the controller.
     *
     * @param id Unique ID of the device
     * @return HTTP status of the request.
     * @throws IOException if the request could not be executed due to cancellation, a connectivity problem or timeout.
     */
    public HttpResponse<Void> deleteDevice(String id) throws IOException {
        return delete("/Devices/" + id, Void.class);
    }

    public HttpResponse<List<EndpointApp>> getEndpointApps() throws IOException {
        HttpResponse<EndpointAppListResponse> httpResponse = get("/EndpointApps", EndpointAppListResponse.class);

        HttpResponse<List<EndpointApp>> newResponse = new HttpResponse<>();
        newResponse.setStatusCode(httpResponse.getStatusCode());
        newResponse.setMessage(httpResponse.getMessage());
        newResponse.setBody(httpResponse.getBody().getResources());

        return newResponse;
    }

    public HttpResponse<EndpointApp> getEndpointApp(String id) throws IOException {
        return get("/EndpointApps/" + id, EndpointApp.class);
    }

    public HttpResponse<EndpointApp> createEndpointApp(EndpointApp endpointApp) throws IOException {
        return post("/EndpointApps", endpointApp, EndpointApp.class);
    }
}
