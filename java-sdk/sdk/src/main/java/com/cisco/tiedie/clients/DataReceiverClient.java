// Copyright (c) 2023, Cisco and/or its affiliates.
// All rights reserved.
// See license in distribution for details.

package com.cisco.tiedie.clients;

import com.cisco.tiedie.auth.Authenticator;
import com.cisco.tiedie.proto.DataSubscription;
import lombok.NonNull;

import org.eclipse.paho.client.mqttv3.IMqttMessageListener;
import org.eclipse.paho.client.mqttv3.MqttClient;
import org.eclipse.paho.client.mqttv3.MqttConnectOptions;
import org.eclipse.paho.client.mqttv3.persist.MemoryPersistence;

import java.util.List;
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
            if (!topic.equals(receivedTopic)) {
                return;
            }

            byte[] payload = message.getPayload();

            DataSubscription dataSubscription = DataSubscription.parseFrom(payload);

            callback.accept(dataSubscription);
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
            var topic = topicsArray[i];
            mqttListeners[i] = (receivedTopic, message) -> {
                if (!topic.equals(receivedTopic)) {
                    return;
                }

                byte[] payload = message.getPayload();

                DataSubscription dataSubscription = DataSubscription.parseFrom(payload);

                callback.accept(dataSubscription, topic);
            };
        }

        mqttClient.subscribe(topicsArray, mqttListeners);
    }

    /**
     * Unsubscribe from a topic.
     * 
     * @param topic The topic to subscribe on
     * @throws Exception if any MQTT problem was encountered
     */
    public void unsubscribe(String topic) throws Exception {
        mqttClient.unsubscribe(topic);
    }
}
