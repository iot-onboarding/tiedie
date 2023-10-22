// Copyright (c) 2023, Cisco and/or its affiliates.
// All rights reserved.
// See license in distribution for details.

package com.cisco.tiedie.auth;

import lombok.AccessLevel;
import lombok.AllArgsConstructor;
import okhttp3.OkHttpClient;
import org.eclipse.paho.client.mqttv3.MqttConnectOptions;

import javax.naming.InvalidNameException;
import javax.naming.ldap.LdapName;
import javax.naming.ldap.Rdn;
import javax.net.ssl.KeyManager;
import javax.net.ssl.SSLContext;
import javax.net.ssl.TrustManager;
import javax.net.ssl.X509TrustManager;
import javax.security.auth.x500.X500Principal;
import java.io.InputStream;
import java.security.KeyStore;
import java.security.KeyStoreException;
import java.security.cert.X509Certificate;
import java.util.Enumeration;
import java.util.Optional;

/**
 * Client authentication method using certificates.
 * <p>
 * To create a {@link CertificateAuthenticator}, use the {@link CertificateAuthenticator#create(InputStream, KeyStore, String)} method:
 * <pre>
 * {@code
 * KeyStore keyStore = ...;
 * var authenticator = CertificateAuthenticator.create(inputStream, keyStore, "password");
 * }
 * </pre>
 */
@AllArgsConstructor(access = AccessLevel.PRIVATE)
public class CertificateAuthenticator implements Authenticator {

    private KeyManager[] keyManagers;
    private TrustManager[] trustManagers;

    private String cn;

    private static String getCnFromKeyStore(KeyStore keyStore) {
        try {
            Enumeration<String> aliases = keyStore.aliases();
            String alias = aliases.nextElement();

            X509Certificate certificate = (X509Certificate) keyStore.getCertificate(alias);
            X500Principal principal = certificate.getSubjectX500Principal();

            LdapName ldapName = new LdapName(principal.getName());

            Optional<Rdn> rdn = ldapName.getRdns().stream().filter(i -> i.getType().equalsIgnoreCase("CN"))
                    .findFirst();

            if (rdn.isEmpty()) {
                throw new RuntimeException("No CN found in certificate");
            }

            return rdn.get().getValue().toString();
        } catch (KeyStoreException | InvalidNameException e) {
            throw new RuntimeException(e);
        }
    }

    /**
     * Create a new {@link CertificateAuthenticator} object.
     *
     * @param caInputStream {@link InputStream} that has the contents of the CA file in PEM format.
     * @param keyStore      {@link KeyStore} object that has the certificate and private key to be used by the client.
     * @param password      Password for the {@link KeyStore} object.
     * @return Authenticator object that can be passed to a client.
     */
    public static CertificateAuthenticator create(InputStream caInputStream, KeyStore keyStore, String password) {
        var keyManagers = Authenticator.getKeyManagers(keyStore, password);
        var trustManagers = Authenticator.getCaTrustManagers(caInputStream);

        String cn = getCnFromKeyStore(keyStore);

        return new CertificateAuthenticator(keyManagers, trustManagers, cn);
    }

    @Override
    public String getClientID() {
        return cn;
    }

    @Override
    public OkHttpClient.Builder setAuthOptions(OkHttpClient.Builder builder) {
        try {
            SSLContext sslContext = SSLContext.getInstance("TLS");

            sslContext.init(keyManagers, trustManagers, null);

            if (SKIP_HOSTNAME_VERIFICATION) {
                builder.hostnameVerifier((hostname, session) -> true);
            }

            return builder
                    .sslSocketFactory(sslContext.getSocketFactory(), (X509TrustManager) trustManagers[0]);
        } catch (Exception e) {
            throw new RuntimeException(e);
        }
    }

    @Override
    public void setAuthOptions(MqttConnectOptions mqttConnectOptions) {
        try {
            SSLContext sslContext = SSLContext.getInstance("TLS");

            sslContext.init(keyManagers, trustManagers, null);

            mqttConnectOptions.setHttpsHostnameVerificationEnabled(!SKIP_HOSTNAME_VERIFICATION);
            mqttConnectOptions.setUserName(getClientID());
            mqttConnectOptions.setSocketFactory(sslContext.getSocketFactory());
        } catch (Exception e) {
            throw new RuntimeException(e);
        }
    }
}
