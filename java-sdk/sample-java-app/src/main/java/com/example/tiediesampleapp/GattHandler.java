// Copyright (c) 2023, Cisco and/or its affiliates.
// All rights reserved.
// See LICENSE file in this distribution.
// SPDX-License-Identifier: Apache-2.0

package com.example.tiediesampleapp;

import java.util.Map;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.server.ServerHttpRequest;
import org.springframework.http.server.ServerHttpResponse;
import org.springframework.stereotype.Component;
import org.springframework.web.socket.CloseStatus;
import org.springframework.web.socket.TextMessage;
import org.springframework.web.socket.WebSocketHandler;
import org.springframework.web.socket.WebSocketSession;
import org.springframework.web.socket.handler.TextWebSocketHandler;
import org.springframework.web.socket.server.HandshakeInterceptor;

import com.cisco.tiedie.clients.DataReceiverClient;
import com.google.protobuf.util.JsonFormat;

@Component
public class GattHandler extends TextWebSocketHandler implements HandshakeInterceptor {
    @Autowired
    DataReceiverClient dataReceiverClient;

    @Override
    protected void handleTextMessage(WebSocketSession session, TextMessage message) throws Exception {
        if (!session.isOpen()) {
            return;
        }

        dataReceiverClient.connect();

        var topic = (String) session.getAttributes().get("topic");

        System.out.println("Subscribing to topic: " + topic);

        dataReceiverClient.subscribe(topic, (dataSubscription) -> {
            try {
                var payload = JsonFormat.printer().print(dataSubscription);
                if (session.isOpen()) {
                    session.sendMessage(new TextMessage(payload));
                }
            } catch (Exception e) {
                e.printStackTrace();
            }
        });
    }

    @Override
    public boolean beforeHandshake(ServerHttpRequest request, ServerHttpResponse response, WebSocketHandler wsHandler,
            Map<String, Object> attributes) throws Exception {
        String path = request.getURI().getPath();

        String topic = path.replace("/subscription/", "");
        attributes.put("topic", topic);

        return true;
    }

    @Override
    public void afterHandshake(ServerHttpRequest request, ServerHttpResponse response, WebSocketHandler wsHandler,
            Exception exception) {
    }

    @Override
    public void afterConnectionClosed(WebSocketSession session, CloseStatus status) throws Exception {
        var topic = (String) session.getAttributes().get("topic");

        dataReceiverClient.unsubscribe(topic);
    }
}
