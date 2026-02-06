// Copyright (c) 2023, Cisco Systems, Inc. and/or its affiliates.
// All rights reserved.
// See LICENSE file in this distribution.
// SPDX-License-Identifier: Apache-2.0

package com.example.tiediesampleapp.service;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.oauth2.client.AuthorizedClientServiceOAuth2AuthorizedClientManager;
import org.springframework.security.oauth2.client.OAuth2AuthorizeRequest;
import org.springframework.security.oauth2.client.OAuth2AuthorizedClientManager;
import org.springframework.security.oauth2.client.OAuth2AuthorizedClientProviderBuilder;
import org.springframework.security.oauth2.client.OAuth2AuthorizedClientService;
import org.springframework.security.oauth2.client.InMemoryOAuth2AuthorizedClientService;
import org.springframework.security.oauth2.client.endpoint.DefaultAuthorizationCodeTokenResponseClient;
import org.springframework.security.oauth2.client.registration.ClientRegistration;
import org.springframework.security.oauth2.client.registration.InMemoryClientRegistrationRepository;
import org.springframework.security.oauth2.core.AuthorizationGrantType;
import org.springframework.security.oauth2.core.ClientAuthenticationMethod;
import org.springframework.security.oauth2.core.endpoint.OAuth2AuthorizationRequest;
import org.springframework.security.oauth2.core.endpoint.OAuth2AuthorizationResponse;
import org.springframework.security.oauth2.client.endpoint.OAuth2AuthorizationCodeGrantRequest;
import org.springframework.security.oauth2.core.endpoint.OAuth2AuthorizationExchange;
import org.springframework.stereotype.Service;

import java.time.Duration;
import java.util.Arrays;
import java.util.Set;
import java.util.stream.Collectors;
import java.util.UUID;

@Service
public class OAuthService {
    private static final String REGISTRATION_ID = "tiedie";
    private static final String PRINCIPAL_NAME = "sample-user";
    private static final Authentication PRINCIPAL = new UsernamePasswordAuthenticationToken(
            PRINCIPAL_NAME,
            "N/A",
            java.util.List.of(new SimpleGrantedAuthority("ROLE_USER"))
    );

    @Value("${oauth.client-id:#{null}}")
    private String clientId;

    @Value("${oauth.client-secret:#{null}}")
    private String clientSecret;

    @Value("${oauth.auth-endpoint:#{null}}")
    private String authEndpoint;

    @Value("${oauth.token-endpoint:#{null}}")
    private String tokenEndpoint;

    @Value("${oauth.redirect-uri:#{null}}")
    private String redirectUri;

    @Value("${oauth.scopes:#{null}}")
    private String scopes;

    private final Object lock = new Object();
    private final DefaultAuthorizationCodeTokenResponseClient authorizationCodeTokenResponseClient =
            new DefaultAuthorizationCodeTokenResponseClient();

    private volatile ClientRegistration clientRegistration;
    private volatile OAuth2AuthorizedClientService authorizedClientService;
    private volatile OAuth2AuthorizedClientManager authorizedClientManager;

    public boolean isEnabled() {
        return hasValue(clientId)
                && hasValue(clientSecret)
                && hasValue(authEndpoint)
                && hasValue(tokenEndpoint)
                && hasValue(redirectUri);
    }

    public boolean hasValidToken() {
        if (!isEnabled()) {
            return true;
        }

        try {
            String token = getAccessToken();
            return token != null && !token.isBlank();
        } catch (Exception ignored) {
            return false;
        }
    }

    public String createState() {
        return UUID.randomUUID().toString();
    }

    public String buildAuthorizationUri(String state) {
        ensureInitialized();
        OAuth2AuthorizationRequest request = OAuth2AuthorizationRequest.authorizationCode()
                .authorizationUri(clientRegistration.getProviderDetails().getAuthorizationUri())
                .clientId(clientRegistration.getClientId())
                .redirectUri(clientRegistration.getRedirectUri())
                .scopes(clientRegistration.getScopes())
                .state(state)
                .build();
        return request.getAuthorizationRequestUri();
    }

    public void exchangeAuthorizationCode(String code) {
        ensureInitialized();

        OAuth2AuthorizationRequest request = OAuth2AuthorizationRequest.authorizationCode()
                .authorizationUri(clientRegistration.getProviderDetails().getAuthorizationUri())
                .clientId(clientRegistration.getClientId())
                .redirectUri(clientRegistration.getRedirectUri())
                .scopes(clientRegistration.getScopes())
                .state("state")
                .build();

        OAuth2AuthorizationResponse response = OAuth2AuthorizationResponse.success(code)
                .redirectUri(clientRegistration.getRedirectUri())
                .state("state")
                .build();

        OAuth2AuthorizationCodeGrantRequest grantRequest = new OAuth2AuthorizationCodeGrantRequest(
                clientRegistration,
                new OAuth2AuthorizationExchange(request, response)
        );

        var tokenResponse = authorizationCodeTokenResponseClient.getTokenResponse(grantRequest);
        var authorizedClient = new org.springframework.security.oauth2.client.OAuth2AuthorizedClient(
                clientRegistration,
                PRINCIPAL_NAME,
                tokenResponse.getAccessToken(),
                tokenResponse.getRefreshToken()
        );
        authorizedClientService.saveAuthorizedClient(authorizedClient, PRINCIPAL);
    }

    public String getAccessToken() {
        ensureInitialized();

        OAuth2AuthorizeRequest authorizeRequest = OAuth2AuthorizeRequest.withClientRegistrationId(REGISTRATION_ID)
                .principal(PRINCIPAL)
                .build();
        var authorizedClient = authorizedClientManager.authorize(authorizeRequest);
        if (authorizedClient == null || authorizedClient.getAccessToken() == null) {
            throw new IllegalStateException("OAuth access token is missing");
        }

        return authorizedClient.getAccessToken().getTokenValue();
    }

    public void clearTokens() {
        synchronized (lock) {
            if (authorizedClientService != null) {
                authorizedClientService.removeAuthorizedClient(REGISTRATION_ID, PRINCIPAL_NAME);
            }
        }
    }

    private void ensureInitialized() {
        if (!isEnabled()) {
            throw new IllegalStateException("OAuth is not configured");
        }

        if (authorizedClientManager != null) {
            return;
        }

        synchronized (lock) {
            if (authorizedClientManager != null) {
                return;
            }

            clientRegistration = ClientRegistration.withRegistrationId(REGISTRATION_ID)
                    .clientName("TieDie OAuth")
                    .clientId(clientId)
                    .clientSecret(clientSecret)
                    .clientAuthenticationMethod(ClientAuthenticationMethod.CLIENT_SECRET_POST)
                    .authorizationGrantType(AuthorizationGrantType.AUTHORIZATION_CODE)
                    .redirectUri(redirectUri)
                    .scope(parseScopes(scopes))
                    .authorizationUri(authEndpoint)
                    .tokenUri(tokenEndpoint)
                    .build();

            var registrationRepository = new InMemoryClientRegistrationRepository(clientRegistration);
            authorizedClientService = new InMemoryOAuth2AuthorizedClientService(registrationRepository);

            var manager = new AuthorizedClientServiceOAuth2AuthorizedClientManager(
                    registrationRepository,
                    authorizedClientService
            );
            var provider = OAuth2AuthorizedClientProviderBuilder.builder()
                    .refreshToken(refresh -> refresh.clockSkew(Duration.ofSeconds(30)))
                    .build();
            manager.setAuthorizedClientProvider(provider);
            authorizedClientManager = manager;
        }
    }

    private Set<String> parseScopes(String scopeProperty) {
        if (!hasValue(scopeProperty)) {
            return Set.of();
        }

        return Arrays.stream(scopeProperty.replace(',', ' ').split("\\s+"))
                .filter(OAuthService::hasValue)
                .collect(Collectors.toSet());
    }

    private static boolean hasValue(String value) {
        return value != null && !value.isBlank();
    }
}
