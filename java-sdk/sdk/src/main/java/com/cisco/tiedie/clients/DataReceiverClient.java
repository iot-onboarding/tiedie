// Copyright (c) 2023, Cisco Systems, Inc. and/or its affiliates.
// All rights reserved.
// See LICENSE file in this distribution.
// SPDX-License-Identifier: Apache-2.0

package com.cisco.tiedie.clients;

import com.cisco.tiedie.auth.Authenticator;
import com.cisco.tiedie.dto.telemetry.DataSubscription;
import com.cisco.tiedie.utils.ObjectMapperSingleton;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.JsonNode;

import lombok.NonNull;

import org.eclipse.paho.client.mqttv3.IMqttMessageListener;
import org.eclipse.paho.client.mqttv3.MqttClient;
import org.eclipse.paho.client.mqttv3.MqttConnectOptions;
import org.eclipse.paho.client.mqttv3.persist.MemoryPersistence;

import java.util.List;
import java.util.Locale;
import java.util.ArrayList;
import java.util.Collections;
import java.util.function.BiConsumer;
import java.util.function.Consumer;

/**
 * This class is used to receive telemetry data from the Tiedie controller.
 * 
 * <pre>
 * {@code
 * InputStream caInputStream = new FileInputStream("ca.pem");
 * Authenticator authenticator = ApiKeyAuthenticator.create(caInputStream, "app_id", "api_key");
 *
 * DataReceiverClient dataReceiverClient = new DataReceiverClient("ssl://<host>:8883", authenticator);
 * }
 * </pre>
 * <p>
 * The above example uses an {@link com.cisco.tiedie.auth.ApiKeyAuthenticator}.
 *
 * @see Authenticator
 */
public class DataReceiverClient {
    private final MqttClient mqttClient;
    private final MqttConnectOptions mqttConnectOptions;

    private final ObjectMapper mapper = ObjectMapperSingleton.getCborInstance();

    /**
     * Create a {@link DataReceiverClient} object.
     *
     * @param baseUrl       The TieDie MQTT broker URL.
     * @param authenticator {@link Authenticator} object that describes the
     *                      authentication mechanism used.
     * @throws Exception if any MQTT problem was encountered
     */
    public DataReceiverClient(String baseUrl, Authenticator authenticator) throws Exception {
        MemoryPersistence persistence = new MemoryPersistence();

        this.mqttClient = new MqttClient(baseUrl, authenticator.getClientID(), persistence);

        this.mqttConnectOptions = new MqttConnectOptions();
        mqttConnectOptions.setAutomaticReconnect(true);
        mqttConnectOptions.setCleanSession(true);

        authenticator.setAuthOptions(mqttConnectOptions);

        // For non-TLS broker URIs (e.g. tcp://), Paho rejects SSL socket factories.
        if (!isTlsBrokerUrl(baseUrl)) {
            mqttConnectOptions.setSocketFactory(null);
            mqttConnectOptions.setHttpsHostnameVerificationEnabled(false);
        }
    }

    /**
     * Connect to the MQTT broker
     *
     * @throws Exception if any MQTT problem was encountered
     */
    public void connect() throws Exception {
        if (mqttClient.isConnected()) {
            return;
        }
        mqttClient.connect(mqttConnectOptions);
    }

    /**
     * Disconnect from the MQTT broker.
     *
     * @throws Exception if any MQTT problem was encountered
     */
    public void disconnect() throws Exception {
        if (!mqttClient.isConnected()) {
            return;
        }
        mqttClient.disconnect();
    }

    /**
     * @return true if the MQTT client is connected.
     */
    public boolean isConnected() {
        return mqttClient.isConnected();
    }

    /**
     * Subscribe to a topic. The topic must be registered by the control app
     * and this data app has to be registered on that topic for the subscription
     * to be authorized.
     *
     * @param topic    The topic to subscribe on
     * @param callback A callback function that produces a {@link DataSubscription}
     *                 object
     *                 that has the subscription data
     * @throws Exception if any MQTT problem was encountered
     */
    public void subscribe(@NonNull String topic, Consumer<DataSubscription> callback) throws Exception {
        mqttClient.subscribe(topic, (receivedTopic, message) -> {
            byte[] payload = message.getPayload();
            List<DataSubscription> dataSubscriptions = decodeDataSubscriptions(payload);
            for (DataSubscription dataSubscription : dataSubscriptions) {
                callback.accept(dataSubscription);
            }
        });
    }

    /**
     * Subscribe to a topic. The topic must be registered by the control app
     * and this data app has to be registered on that topic for the subscription
     * to be authorized.
     *
     * @param topics   The topics to subscribe on
     * @param callback A callback function that produces a {@link DataSubscription}
     *                 object
     *                 that has the subscription data
     * @throws Exception if any MQTT problem was encountered
     */
    public void subscribe(@NonNull List<String> topics, BiConsumer<DataSubscription, String> callback)
            throws Exception {
        var topicsArray = topics.toArray(new String[0]);

        // create mqtt listener array for each topic that call the callback function
        var mqttListeners = new IMqttMessageListener[topicsArray.length];
        for (int i = 0; i < topicsArray.length; i++) {
            mqttListeners[i] = (receivedTopic, message) -> {
                byte[] payload = message.getPayload();
                List<DataSubscription> dataSubscriptions = decodeDataSubscriptions(payload);
                for (DataSubscription dataSubscription : dataSubscriptions) {
                    callback.accept(dataSubscription, receivedTopic);
                }
            };
        }

        mqttClient.subscribe(topicsArray, mqttListeners);
    }

    /**
     * Unsubscribe from a topic.
     *
     * @param topic topic to unsubscribe from
     * @throws Exception if any MQTT problem was encountered
     */
    public void unsubscribe(@NonNull String topic) throws Exception {
        if (!mqttClient.isConnected()) {
            return;
        }
        mqttClient.unsubscribe(topic);
    }

    /**
     * Unsubscribe from multiple topics.
     *
     * @param topics topics to unsubscribe from
     * @throws Exception if any MQTT problem was encountered
     */
    public void unsubscribe(@NonNull List<String> topics) throws Exception {
        if (!mqttClient.isConnected() || topics.isEmpty()) {
            return;
        }
        mqttClient.unsubscribe(topics.toArray(new String[0]));
    }

    private static boolean isTlsBrokerUrl(String baseUrl) {
        if (baseUrl == null) {
            return false;
        }

        String normalized = baseUrl.trim().toLowerCase(Locale.ROOT);
        return normalized.startsWith("ssl://")
                || normalized.startsWith("tls://")
                || normalized.startsWith("wss://")
                || normalized.startsWith("mqtts://");
    }

    private List<DataSubscription> decodeDataSubscriptions(byte[] payload) throws Exception {
        if (payload == null || payload.length == 0) {
            return Collections.emptyList();
        }

        JsonNode root = mapper.readTree(payload);
        if (root == null || root.isNull()) {
            return Collections.emptyList();
        }

        if (root.isArray()) {
            return mapper.convertValue(root, new TypeReference<List<DataSubscription>>() {});
        }

        List<DataSubscription> subscriptions = new ArrayList<>(1);
        subscriptions.add(mapper.treeToValue(root, DataSubscription.class));
        return subscriptions;
    }
}
