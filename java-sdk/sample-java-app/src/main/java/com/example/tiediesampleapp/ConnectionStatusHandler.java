// Copyright (c) 2023, Cisco and/or its affiliates.
// All rights reserved.
// See LICENSE file in this distribution.
// SPDX-License-Identifier: Apache-2.0

package com.example.tiediesampleapp;

import java.util.List;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;
import org.springframework.web.socket.TextMessage;
import org.springframework.web.socket.WebSocketSession;
import org.springframework.web.socket.handler.TextWebSocketHandler;

import com.cisco.tiedie.clients.DataReceiverClient;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.google.protobuf.util.JsonFormat;

@Component
public class ConnectionStatusHandler extends TextWebSocketHandler {

    @Autowired
    DataReceiverClient dataReceiverClient;

    @Override
    protected void handleTextMessage(WebSocketSession session, TextMessage message) throws Exception {
        if (!session.isOpen()) {
            return;
        }

        String str = message.getPayload();

        ObjectMapper mapper = new ObjectMapper();
        var topics = mapper.readValue(str, new TypeReference<List<String>>() {
        });

        dataReceiverClient.connect();
        dataReceiverClient.subscribe(topics, (dataSubscription, topic) -> {
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
}
