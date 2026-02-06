// Copyright (c) 2023, Cisco Systems, Inc. and/or its affiliates.
// All rights reserved.
// See LICENSE file in this distribution.
// SPDX-License-Identifier: Apache-2.0

package com.example.tiediesampleapp.controller;

import com.example.tiediesampleapp.service.OAuthService;
import com.example.tiediesampleapp.service.TiedieClientManager;
import jakarta.servlet.http.HttpSession;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestParam;

@Controller
public class OAuthController {
    private static final String OAUTH_STATE_KEY = "oauth_state";

    private final OAuthService oAuthService;
    private final TiedieClientManager tiedieClientManager;

    public OAuthController(OAuthService oAuthService, TiedieClientManager tiedieClientManager) {
        this.oAuthService = oAuthService;
        this.tiedieClientManager = tiedieClientManager;
    }

    @GetMapping("/oauth2/authorize")
    public String oauthAuthorizePage() {
        if (!oAuthService.isEnabled()) {
            return "redirect:/devices";
        }

        if (tiedieClientManager.hasOauthToken()) {
            return "redirect:/devices";
        }

        return "oauth2_authorize";
    }

    @PostMapping("/oauth2/authorize")
    public String oauthAuthorize(HttpSession session, Model model) {
        if (!oAuthService.isEnabled()) {
            return "redirect:/devices";
        }

        try {
            String state = oAuthService.createState();
            session.setAttribute(OAUTH_STATE_KEY, state);
            return "redirect:" + oAuthService.buildAuthorizationUri(state);
        } catch (Exception e) {
            model.addAttribute("error", "Failed to start OAuth flow: " + e.getMessage());
            return "error";
        }
    }

    @GetMapping("/oauth_callback")
    public String oauthCallback(
            @RequestParam(name = "code", required = false) String code,
            @RequestParam(name = "state", required = false) String state,
            @RequestParam(name = "error", required = false) String error,
            HttpSession session,
            Model model
    ) {
        if (error != null) {
            model.addAttribute("error", "OAuth authorization failed: " + error);
            return "error";
        }

        String expectedState = (String) session.getAttribute(OAUTH_STATE_KEY);
        if (expectedState != null && !expectedState.equals(state)) {
            model.addAttribute("error", "OAuth callback state mismatch");
            return "error";
        }

        if (code == null || code.isBlank()) {
            model.addAttribute("error", "OAuth callback did not include an authorization code");
            return "error";
        }

        try {
            oAuthService.exchangeAuthorizationCode(code);
            tiedieClientManager.invalidate();
            return "redirect:/devices";
        } catch (Exception e) {
            model.addAttribute("error", "OAuth token exchange failed: " + e.getMessage());
            return "error";
        } finally {
            session.removeAttribute(OAUTH_STATE_KEY);
        }
    }
}
