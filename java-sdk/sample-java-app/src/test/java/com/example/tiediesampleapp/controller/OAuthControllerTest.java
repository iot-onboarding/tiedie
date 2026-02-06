// Copyright (c) 2023, Cisco Systems, Inc. and/or its affiliates.
// All rights reserved.
// See LICENSE file in this distribution.
// SPDX-License-Identifier: Apache-2.0

package com.example.tiediesampleapp.controller;

import com.example.tiediesampleapp.service.OAuthService;
import com.example.tiediesampleapp.service.TiedieClientManager;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.mock.web.MockHttpSession;
import org.springframework.test.web.servlet.MockMvc;

import static org.hamcrest.Matchers.containsString;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.content;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.redirectedUrl;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@SpringBootTest
@AutoConfigureMockMvc
class OAuthControllerTest {
    @Autowired
    private MockMvc mockMvc;

    @MockBean
    private TiedieClientManager tiedieClientManager;

    @MockBean
    private OAuthService oAuthService;

    @BeforeEach
    void setUp() {
        when(tiedieClientManager.isOauthEnabled()).thenReturn(true);
        when(tiedieClientManager.hasOauthToken()).thenReturn(false);
    }

    @Test
    void authorizeRedirectsToProvider() throws Exception {
        when(oAuthService.isEnabled()).thenReturn(true);
        when(oAuthService.createState()).thenReturn("state-1");
        when(oAuthService.buildAuthorizationUri("state-1")).thenReturn("https://auth.example.com/authorize");

        mockMvc.perform(post("/oauth2/authorize"))
                .andExpect(status().is3xxRedirection())
                .andExpect(redirectedUrl("https://auth.example.com/authorize"));
    }

    @Test
    void authorizePageRendersWhenTokenMissing() throws Exception {
        when(oAuthService.isEnabled()).thenReturn(true);

        mockMvc.perform(get("/oauth2/authorize"))
                .andExpect(status().isOk())
                .andExpect(content().string(containsString("OAuth2 Authorization")));
    }

    @Test
    void callbackExchangesCodeAndInvalidatesClients() throws Exception {
        when(oAuthService.isEnabled()).thenReturn(true);
        MockHttpSession session = new MockHttpSession();
        session.setAttribute("oauth_state", "state-1");

        mockMvc.perform(get("/oauth_callback")
                        .session(session)
                        .param("code", "code-1")
                        .param("state", "state-1"))
                .andExpect(status().is3xxRedirection())
                .andExpect(redirectedUrl("/devices"));

        verify(oAuthService).exchangeAuthorizationCode("code-1");
        verify(tiedieClientManager).invalidate();
    }
}
