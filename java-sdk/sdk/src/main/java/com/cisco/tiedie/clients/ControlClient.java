// Copyright (c) 2023, Cisco and/or its affiliates.
// All rights reserved.
// See license in distribution for details.

package com.cisco.tiedie.clients;

import com.cisco.tiedie.auth.Authenticator;
import com.cisco.tiedie.dto.control.*;
import com.cisco.tiedie.dto.control.ble.BleConnectRequest;
import com.cisco.tiedie.dto.control.ble.BleDataParameter;
import com.cisco.tiedie.dto.control.ble.BleDiscoverResponse;
import com.cisco.tiedie.dto.control.internal.*;
import com.cisco.tiedie.dto.control.zigbee.ZigbeeDataParameter;
import com.cisco.tiedie.dto.control.zigbee.ZigbeeDiscoverResponse;
import com.cisco.tiedie.dto.scim.Device;
import okhttp3.MediaType;

import java.io.IOException;
import java.util.List;

/**
 * This class is used to communicate with the TieDie control APIs.
 * Create a Control API client as follows:
 * <pre>
 * {@code
 * InputStream caInputStream = new FileInputStream("ca.pem");
 * Authenticator authenticator = ApiKeyAuthenticator.create(caInputStream, "app_id", "api_key");
 *
 * ControlClient controlClient = new ControlClient("https://<host>/control", authenticator);
 * }
 * </pre>
 * <p>
 * The above example uses an {@link com.cisco.tiedie.auth.ApiKeyAuthenticator}.
 *
 * @see Authenticator
 */
public class ControlClient extends AbstractHttpClient {

    private final String controlAppId;

    /**
     * Create a {@link ControlClient} object.
     *
     * @param baseUrl       The TieDie controller base URL.
     * @param authenticator {@link Authenticator} object that describes the authentication mechanism used.
     */
    public ControlClient(String baseUrl, Authenticator authenticator) {
        super(baseUrl, MediaType.parse("application/json"), authenticator);
        this.controlAppId = authenticator.getClientID();
    }

    /**
     * TieDie Introduce API - used to introduce a device into the enterprise network.
     * <p>
     * For a BLE device, this is equivalent to pairing the device with a central.
     * <p>
     * For a Zigbee device, this will join the zigbee network.
     *
     * @param device The {@link Device} object.
     * @return A {@link TiedieResponse} object.
     * @throws IOException if the request could not be executed due to cancellation, a connectivity problem or timeout.
     */
    public TiedieResponse<Void> introduce(Device device) throws IOException {
        var tiedieRequest = TiedieBasicRequest.createRequest(device, controlAppId);

        return postWithTiedieResponse("/connectivity/introduce", tiedieRequest, Void.class);
    }

    /**
     * TieDie Connect API - used to connect to a particular device.
     * <em>This operation is currently only supported in BLE.</em>
     *
     * @param device The {@link Device} object. Must be a BLE device.
     * @return The parameters that are discovered after the connect procedure.
     * For BLE, this is the GATT database that is discovered.
     * @throws IOException if the request could not be executed due to cancellation, a connectivity problem or timeout.
     * @see ControlClient#connect(Device, BleConnectRequest)
     */
    public TiedieResponse<List<DataParameter>> connect(Device device) throws IOException {
        return connect(device, new BleConnectRequest(null, 3, true));
    }


    /**
     * TieDie Connect API - used to connect to a particular device.
     * <em>This operation is currently only supported in BLE.</em>
     *
     * @param device  The {@link Device} object. Must be a BLE device.
     * @param request Additional BLE connection options.
     * @return The parameters that are discovered after the connect procedure.
     * * For BLE, this is the GATT database that is discovered.
     * @throws IOException if the request could not be executed due to cancellation, a connectivity problem or timeout.
     */
    public TiedieResponse<List<DataParameter>> connect(Device device, BleConnectRequest request) throws IOException {
        var tiedieRequest = TiedieConnectRequest.createRequest(device, request, controlAppId);

        var bleDiscoverResponse = postWithTiedieResponse("/connectivity/connect", tiedieRequest, BleDiscoverResponse.class);

        TiedieResponse<List<DataParameter>> response = new TiedieResponse<>();
        response.setHttpStatusCode(bleDiscoverResponse.getHttpStatusCode());
        response.setHttpMessage(bleDiscoverResponse.getHttpMessage());
        response.setStatus(bleDiscoverResponse.getStatus());
        response.setReason(bleDiscoverResponse.getReason());
        response.setErrorCode(bleDiscoverResponse.getErrorCode());

        if (bleDiscoverResponse.getBody() != null && bleDiscoverResponse.getBody().getServices() != null) {
            response.setBody(bleDiscoverResponse.getBody().toParameterList(device.getId()));
        }

        return response;
    }

    /**
     * TieDie Disconnect API - used to disconnect a device.
     * <em>This operation is currently only supported in BLE.</em>
     *
     * @param device The {@link Device} object. Must be a BLE device.
     * @return A {@link TiedieResponse} object.
     * @throws IOException if the request could not be executed due to cancellation, a connectivity problem or timeout.
     */
    public TiedieResponse<Void> disconnect(Device device) throws IOException {
        var tiedieRequest = TiedieBasicRequest.createRequest(device, controlAppId);

        return postWithTiedieResponse("/connectivity/disconnect", tiedieRequest, Void.class);
    }

    /**
     * TieDie Discover API - used to discover the parameters of a {@link Device}.
     * <p>
     * If the device is a BLE device, this is the GATT table of the device. The response includes the primary services
     * and characteristics supported by the BLE device.
     * <p>
     * If the device is a Zigbee device, this is the supported list of endpoints, clusters and attributes.
     *
     * @param device The {@link Device} object.
     * @return If the device is BLE, the response is a list of {@link BleDataParameter}.
     * If the device is Zigbee, the response is a list of {@link ZigbeeDataParameter}.
     * @throws IOException if the request could not be executed due to cancellation, a connectivity problem or timeout.
     */
    public TiedieResponse<List<DataParameter>> discover(Device device) throws IOException {
        return discover(device, null);
    }

    /**
     * TieDie Discover API - used to discover the parameters of a {@link Device}.
     * <p>
     * If the device is a BLE device, this is the GATT table of the device. The response includes the primary services
     * and characteristics supported by the BLE device.
     * <p>
     * If the device is a Zigbee device, this is the supported list of endpoints, clusters and attributes.
     *
     * @param device The {@link Device} object.
     * @param parameters List of data parameters to be discovered
     * @return If the device is BLE, the response is a list of {@link BleDataParameter}.
     * If the device is Zigbee, the response is a list of {@link ZigbeeDataParameter}.
     * @throws IOException if the request could not be executed due to cancellation, a connectivity problem or timeout.
     */
    public TiedieResponse<List<DataParameter>> discover(Device device, List<DataParameter> parameters) throws IOException {
        var tiedieRequest = TiedieDiscoverRequest.createRequest(device, parameters, controlAppId);

        if (tiedieRequest.getTechnology() == Technology.BLE) {
            var bleDiscoverResponse = postWithTiedieResponse("/data/discover", tiedieRequest, BleDiscoverResponse.class);
            TiedieResponse<List<DataParameter>> response = new TiedieResponse<>();
            response.setHttpStatusCode(bleDiscoverResponse.getHttpStatusCode());
            response.setHttpMessage(bleDiscoverResponse.getHttpMessage());
            response.setStatus(bleDiscoverResponse.getStatus());
            response.setReason(bleDiscoverResponse.getReason());
            response.setErrorCode(bleDiscoverResponse.getErrorCode());

            if (bleDiscoverResponse.getBody() != null && bleDiscoverResponse.getBody().getServices() != null) {
                response.setBody(bleDiscoverResponse.getBody().toParameterList(device.getId()));
            }
            return response;
        }

        var zigbeeDiscoverResponse = postWithTiedieResponse("/data/discover", tiedieRequest, ZigbeeDiscoverResponse.class);

        TiedieResponse<List<DataParameter>> response = new TiedieResponse<>();
        response.setHttpStatusCode(zigbeeDiscoverResponse.getHttpStatusCode());
        response.setHttpMessage(zigbeeDiscoverResponse.getHttpMessage());
        response.setStatus(zigbeeDiscoverResponse.getStatus());
        response.setReason(zigbeeDiscoverResponse.getReason());
        response.setErrorCode(zigbeeDiscoverResponse.getErrorCode());

        if (zigbeeDiscoverResponse.getBody() != null && zigbeeDiscoverResponse.getBody().getEndpoints() != null) {
            response.setBody(zigbeeDiscoverResponse.getBody().toParameterList(device.getId()));
        }
        return response;
    }


    /**
     * TieDie Read API - This API is used to read a particular value from the {@link Device}.
     * <p>
     * If the device is a BLE device, this API can be used to read GATT characteristic values.
     * <p>
     * If the device is a Zigbee device, this API can be used to read a cluster attribute value.
     *
     * @param dataParameter A {@link DataParameter} object that was discovered previously.
     * @return If the request was successful, the response has the value that was read from the device.
     * The value is the raw byte value in hex format.
     * @throws IOException if the request could not be executed due to cancellation, a connectivity problem or timeout.
     */
    public TiedieResponse<DataResponse> read(DataParameter dataParameter) throws IOException {
        var tiedieRequest = TiedieReadRequest.createRequest(dataParameter, controlAppId);

        return postWithTiedieResponse("/data/read", tiedieRequest, DataResponse.class);
    }

    /**
     * TieDie Write API - This API is used to write a particular value from the {@link Device}.
     * <p>
     * If the device is a BLE device, this API can be used to write GATT characteristic values.
     * <p>
     * If the device is a Zigbee device, this API can be used to write a cluster attribute value.
     *
     * @param dataParameter A {@link DataParameter} object that was discovered previously.
     * @param value         The value that needs to be written to the device.
     *                      This value needs to be the raw byte value encoded in hex.
     * @return If the request was successful, the response has the value that was written to the device.
     * The value is the raw byte value in hex format.
     * @throws IOException if the request could not be executed due to cancellation, a connectivity problem or timeout.
     */
    public TiedieResponse<DataResponse> write(DataParameter dataParameter, String value) throws IOException {
        var tiedieRequest = TiedieWriteRequest.createRequest(dataParameter, value, controlAppId);

        return postWithTiedieResponse("/data/write", tiedieRequest, DataResponse.class);
    }

    /**
     * TieDie Subscribe API - This API is used to subscribe to data from the {@link Device}.
     * If the device is a BLE device, this API can be used to subscribe to GATT notifications/indications.
     * If the device is a Zigbee device, this API can be used to subscribe to Zigbee attribute reports.
     *
     * @param dataParameter A {@link DataParameter} object that was discovered previously.
     * @return A {@link TiedieResponse} object.
     * @throws IOException if the request could not be executed due to cancellation, a connectivity problem or timeout.
     * @see ControlClient#subscribe(DataParameter, SubscriptionOptions)
     */
    public TiedieResponse<Void> subscribe(DataParameter dataParameter) throws IOException {
        return subscribe(dataParameter, null);
    }

    /**
     * TieDie Subscribe API - This API is used to subscribe to data from the {@link Device}.
     * <p>
     * If the device is a BLE device, this API can be used to subscribe to GATT notifications/indications.
     * <p>
     * If the device is a Zigbee device, this API can be used to subscribe to Zigbee attribute reports.
     *
     * @param dataParameter A {@link DataParameter} object that was discovered previously.
     * @param options       A {@link SubscriptionOptions} object. This has additional parameters such as the topic,
     *                      data format and additional parameters for Zigbee.
     * @return A {@link TiedieResponse} object.
     * @throws IOException if the request could not be executed due to cancellation, a connectivity problem or timeout.
     */
    public TiedieResponse<Void> subscribe(DataParameter dataParameter, SubscriptionOptions options) throws IOException {
        var tiedieRequest = TiedieSubscribeRequest.createRequest(dataParameter, controlAppId, options);

        return postWithTiedieResponse("/data/subscribe", tiedieRequest, Void.class);
    }

    /**
     * TieDie Unsubscribe API - This API is used to unsubscribe to data from the {@link Device}.
     * <p>
     * If the device is a BLE device, this API can be used to unsubscribe from GATT notifications/indications.
     * <p>
     * If the device is a Zigbee device, this API can be used to unsubscribe from Zigbee attribute reports.
     *
     * @param dataParameter A {@link DataParameter} object that was discovered previously.
     * @return A {@link TiedieResponse} object.
     * @throws IOException if the request could not be executed due to cancellation, a connectivity problem or timeout.
     */
    public TiedieResponse<Void> unsubscribe(DataParameter dataParameter) throws IOException {
        var tiedieRequest = TiedieUnsubscribeRequest.createRequest(dataParameter, controlAppId);

        return postWithTiedieResponse("/data/unsubscribe", tiedieRequest, Void.class);
    }

    public TiedieResponse<Void> registerTopic(String topic, RegistrationOptions options) throws IOException {
        var tiedieRequest = TiedieRegisterTopicRequest.createRequest(topic, options, controlAppId);

        return postWithTiedieResponse("/registration/registerTopic", tiedieRequest, Void.class);
    }

    public TiedieResponse<Void> unregisterTopic(String topic, List<String> devices) throws IOException {
        var tiedieRequest = TiedieUnregisterTopicRequest.createRequest(topic, devices, controlAppId);

        return postWithTiedieResponse("/registration/unregisterTopic", tiedieRequest, Void.class);
    }

    public TiedieResponse<Void> registerDataApp(String dataApp, String topic) throws IOException {
        var tiedieRequest = TiedieRegisterDataAppRequest.createRequest(dataApp, topic, controlAppId);

        return postWithTiedieResponse("/registration/registerDataApp", tiedieRequest, Void.class);
    }
}
