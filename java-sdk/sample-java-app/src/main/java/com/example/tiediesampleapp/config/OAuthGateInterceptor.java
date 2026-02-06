// Copyright (c) 2023, Cisco Systems, Inc. and/or its affiliates.
// All rights reserved.
// See LICENSE file in this distribution.
// SPDX-License-Identifier: Apache-2.0

package com.example.tiediesampleapp.config;

import com.example.tiediesampleapp.service.TiedieClientManager;
import org.springframework.stereotype.Component;
import org.springframework.web.servlet.HandlerInterceptor;

import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;

@Component
public class OAuthGateInterceptor implements HandlerInterceptor {
    private final TiedieClientManager tiedieClientManager;

    public OAuthGateInterceptor(TiedieClientManager tiedieClientManager) {
        this.tiedieClientManager = tiedieClientManager;
    }

    @Override
    public boolean preHandle(HttpServletRequest request, HttpServletResponse response, Object handler) throws Exception {
        if (!tiedieClientManager.isOauthEnabled()) {
            return true;
        }

        String path = request.getRequestURI();
        if (path.startsWith("/oauth")
                || path.startsWith("/error")
                || path.startsWith("/actuator")
                || path.startsWith("/webjars")) {
            return true;
        }

        if (tiedieClientManager.hasOauthToken()) {
            return true;
        }

        response.sendRedirect("/oauth2/authorize");
        return false;
    }
}
