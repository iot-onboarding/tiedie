// Copyright (c) 2023, Cisco Systems, Inc. and/or its affiliates.
// All rights reserved.
// See LICENSE file in this distribution.
// SPDX-License-Identifier: Apache-2.0

package com.example.tiediesampleapp;

import com.cisco.tiedie.clients.DataReceiverClient;
import com.example.tiediesampleapp.service.TiedieClientManager;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.http.server.ServerHttpRequest;
import org.springframework.http.server.ServerHttpResponse;
import org.springframework.stereotype.Component;
import org.springframework.web.socket.CloseStatus;
import org.springframework.web.socket.TextMessage;
import org.springframework.web.socket.WebSocketHandler;
import org.springframework.web.socket.WebSocketSession;
import org.springframework.web.socket.handler.TextWebSocketHandler;
import org.springframework.web.socket.server.HandshakeInterceptor;
import org.springframework.web.util.UriComponentsBuilder;
import org.springframework.web.util.UriUtils;

import java.nio.charset.StandardCharsets;
import java.util.Map;
import java.util.concurrent.atomic.AtomicInteger;

@Component
public class GattHandler extends TextWebSocketHandler implements HandshakeInterceptor {
    private static final String TOPIC_ATTRIBUTE = "topic";
    private static final String SUBSCRIBED_ATTRIBUTE = "subscribed";

    private final TiedieClientManager tiedieClientManager;
    private final ObjectMapper mapper = new ObjectMapper();
    private final AtomicInteger activeSubscriptions = new AtomicInteger(0);

    public GattHandler(TiedieClientManager tiedieClientManager) {
        this.tiedieClientManager = tiedieClientManager;
    }

    @Override
    protected void handleTextMessage(WebSocketSession session, TextMessage message) throws Exception {
        if (!session.isOpen()) {
            return;
        }

        String topic = (String) session.getAttributes().get(TOPIC_ATTRIBUTE);
        if (topic == null || topic.isBlank()) {
            return;
        }

        boolean alreadySubscribed = Boolean.TRUE.equals(session.getAttributes().get(SUBSCRIBED_ATTRIBUTE));
        if (alreadySubscribed) {
            return;
        }

        DataReceiverClient dataReceiverClient = tiedieClientManager.getDataReceiverClient();
        dataReceiverClient.connect();
        dataReceiverClient.subscribe(topic, dataSubscription -> {
            try {
                if (!session.isOpen()) {
                    return;
                }

                var payload = mapper.writeValueAsString(dataSubscription);
                session.sendMessage(new TextMessage(payload));
            } catch (Exception ignored) {
            }
        });

        session.getAttributes().put(SUBSCRIBED_ATTRIBUTE, true);
        activeSubscriptions.incrementAndGet();
    }

    @Override
    public boolean beforeHandshake(
            ServerHttpRequest request,
            ServerHttpResponse response,
            WebSocketHandler wsHandler,
            Map<String, Object> attributes
    ) {
        String rawTopic = UriComponentsBuilder.fromUri(request.getURI())
                .build()
                .getQueryParams()
                .getFirst("event");
        String topic = rawTopic;
        if (rawTopic != null) {
            topic = UriUtils.decode(rawTopic, StandardCharsets.UTF_8);
        }
        attributes.put(TOPIC_ATTRIBUTE, topic);
        attributes.put(SUBSCRIBED_ATTRIBUTE, false);
        return true;
    }

    @Override
    public void afterHandshake(
            ServerHttpRequest request,
            ServerHttpResponse response,
            WebSocketHandler wsHandler,
            Exception exception
    ) {
    }

    @Override
    public void afterConnectionClosed(WebSocketSession session, CloseStatus status) throws Exception {
        String topic = (String) session.getAttributes().get(TOPIC_ATTRIBUTE);
        boolean subscribed = Boolean.TRUE.equals(session.getAttributes().get(SUBSCRIBED_ATTRIBUTE));

        if (!subscribed || topic == null || topic.isBlank()) {
            return;
        }

        DataReceiverClient dataReceiverClient = tiedieClientManager.getDataReceiverClient();
        dataReceiverClient.unsubscribe(topic);

        int remaining = activeSubscriptions.decrementAndGet();
        if (remaining <= 0) {
            activeSubscriptions.set(0);
            dataReceiverClient.disconnect();
        }
    }
}
