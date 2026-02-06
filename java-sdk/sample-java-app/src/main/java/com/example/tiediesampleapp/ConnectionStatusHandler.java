// Copyright (c) 2023, Cisco Systems, Inc. and/or its affiliates.
// All rights reserved.
// See LICENSE file in this distribution.
// SPDX-License-Identifier: Apache-2.0

package com.example.tiediesampleapp;

import com.cisco.tiedie.clients.DataReceiverClient;
import com.example.tiediesampleapp.service.TiedieClientManager;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.stereotype.Component;
import org.springframework.web.socket.CloseStatus;
import org.springframework.web.socket.TextMessage;
import org.springframework.web.socket.WebSocketSession;
import org.springframework.web.socket.handler.TextWebSocketHandler;

import java.util.List;

@Component
public class ConnectionStatusHandler extends TextWebSocketHandler {
    private static final String TOPICS_ATTRIBUTE = "topics";
    private final TiedieClientManager tiedieClientManager;
    private final ObjectMapper mapper = new ObjectMapper();

    public ConnectionStatusHandler(TiedieClientManager tiedieClientManager) {
        this.tiedieClientManager = tiedieClientManager;
    }

    @Override
    protected void handleTextMessage(WebSocketSession session, TextMessage message) throws Exception {
        if (!session.isOpen()) {
            return;
        }

        List<String> topics = mapper.readValue(message.getPayload(), new TypeReference<>() {});
        if (topics.isEmpty()) {
            return;
        }

        DataReceiverClient dataReceiverClient = tiedieClientManager.getDataReceiverClient();
        dataReceiverClient.connect();
        dataReceiverClient.subscribe(topics, (dataSubscription, _topic) -> {
            try {
                if (!session.isOpen()) {
                    return;
                }
                session.sendMessage(new TextMessage(mapper.writeValueAsString(dataSubscription)));
            } catch (Exception ignored) {
            }
        });

        session.getAttributes().put(TOPICS_ATTRIBUTE, topics);
    }

    @Override
    public void afterConnectionClosed(WebSocketSession session, CloseStatus status) throws Exception {
        Object topicsObj = session.getAttributes().get(TOPICS_ATTRIBUTE);
        if (!(topicsObj instanceof List<?> rawTopics) || rawTopics.isEmpty()) {
            return;
        }

        List<String> topics = rawTopics.stream().filter(String.class::isInstance).map(String.class::cast).toList();
        DataReceiverClient dataReceiverClient = tiedieClientManager.getDataReceiverClient();
        dataReceiverClient.unsubscribe(topics);
    }
}
