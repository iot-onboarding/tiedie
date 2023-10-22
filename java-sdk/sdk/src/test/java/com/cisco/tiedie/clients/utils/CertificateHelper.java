package com.cisco.tiedie.clients.utils;

import java.io.ByteArrayInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.StringWriter;
import java.math.BigInteger;
import java.security.KeyPair;
import java.security.KeyPairGenerator;
import java.security.KeyStore;
import java.security.SecureRandom;
import java.security.cert.Certificate;
import java.security.cert.X509Certificate;
import java.util.Date;
import java.util.Calendar;

import org.bouncycastle.asn1.x500.X500Name;
import org.bouncycastle.asn1.x509.BasicConstraints;
import org.bouncycastle.asn1.x509.Extension;
import org.bouncycastle.cert.X509CertificateHolder;
import org.bouncycastle.cert.X509v3CertificateBuilder;
import org.bouncycastle.cert.jcajce.JcaX509CertificateConverter;
import org.bouncycastle.cert.jcajce.JcaX509ExtensionUtils;
import org.bouncycastle.cert.jcajce.JcaX509v3CertificateBuilder;
import org.bouncycastle.openssl.jcajce.JcaPEMWriter;
import org.bouncycastle.operator.ContentSigner;
import org.bouncycastle.operator.jcajce.JcaContentSignerBuilder;
import org.bouncycastle.pkcs.PKCS10CertificationRequest;
import org.bouncycastle.pkcs.PKCS10CertificationRequestBuilder;
import org.bouncycastle.pkcs.jcajce.JcaPKCS10CertificationRequestBuilder;

public class CertificateHelper {
    public static X500Name createX500Name(String cn) {
        return new X500Name("CN=" + cn);
    }

    public static KeyPair createKeyPair() throws Exception {
        KeyPairGenerator keyPairGenerator = KeyPairGenerator.getInstance("RSA");
        keyPairGenerator.initialize(2048);
        return keyPairGenerator.generateKeyPair();
    }

    public static X509Certificate createCaCertificate(KeyPair rootKeyPair, X500Name rootCertSubject) throws Exception {
        ContentSigner rootCertContentSigner = new JcaContentSignerBuilder("SHA256withRSA")
                .build(rootKeyPair.getPrivate());

        Calendar calendar = Calendar.getInstance();
        calendar.add(Calendar.DATE, -1);
        Date startDate = calendar.getTime();

        calendar.add(Calendar.DATE, 1);
        Date endDate = calendar.getTime();

        BigInteger rootSerialNum = new BigInteger(Long.toString(new SecureRandom().nextLong()));

        X509v3CertificateBuilder rootCertBuilder = new JcaX509v3CertificateBuilder(rootCertSubject,
                rootSerialNum,
                startDate, endDate, rootCertSubject, rootKeyPair.getPublic());

        JcaX509ExtensionUtils rootCertExtUtils = new JcaX509ExtensionUtils();
        rootCertBuilder.addExtension(Extension.basicConstraints, true, new BasicConstraints(true));
        rootCertBuilder.addExtension(Extension.subjectKeyIdentifier, false,
                rootCertExtUtils.createSubjectKeyIdentifier(rootKeyPair.getPublic()));

        X509CertificateHolder rootCertHolder = rootCertBuilder.build(rootCertContentSigner);
        X509Certificate rootCert = new JcaX509CertificateConverter()
                .getCertificate(rootCertHolder);

        return rootCert;
    }

    public static X509Certificate createAppCertificate(KeyPair issuedCertKeyPair, String appCN, KeyPair rootKeyPair, X500Name rootCertSubject)
            throws Exception {
        X500Name issuedCertSubject = new X500Name("CN=" + appCN);
        BigInteger issuedCertSerialNum = new BigInteger(Long.toString(new SecureRandom().nextLong()));

        PKCS10CertificationRequestBuilder p10Builder = new JcaPKCS10CertificationRequestBuilder(issuedCertSubject,
                issuedCertKeyPair.getPublic());
        JcaContentSignerBuilder csrBuilder = new JcaContentSignerBuilder("SHA256withRSA");

        ContentSigner csrContentSigner = csrBuilder.build(rootKeyPair.getPrivate());
        PKCS10CertificationRequest csr = p10Builder.build(csrContentSigner);

        Calendar calendar = Calendar.getInstance();
        calendar.add(Calendar.DATE, -1);
        Date startDate = calendar.getTime();

        calendar.add(Calendar.DATE, 1);
        Date endDate = calendar.getTime();

        X509v3CertificateBuilder issuedCertBuilder = new X509v3CertificateBuilder(rootCertSubject, issuedCertSerialNum,
                startDate, endDate, csr.getSubject(), csr.getSubjectPublicKeyInfo());

        issuedCertBuilder.addExtension(Extension.basicConstraints, true, new BasicConstraints(false));

        X509CertificateHolder issuedCertHolder = issuedCertBuilder.build(csrContentSigner);
        X509Certificate issuedCert = new JcaX509CertificateConverter()
                .getCertificate(issuedCertHolder);

        return issuedCert;
    }

    public static InputStream createPemInputStream(final X509Certificate cert) throws IOException {
        final StringWriter writer = new StringWriter();
        final JcaPEMWriter pemWriter = new JcaPEMWriter(writer);
        pemWriter.writeObject(cert);
        pemWriter.flush();
        pemWriter.close();
        return new ByteArrayInputStream(writer.toString().getBytes("UTF-8"));
    }

    public static KeyStore createKeyStore(KeyPair keyPair, Certificate certificate, String alias) throws Exception {
        KeyStore keyStore = KeyStore.getInstance("PKCS12");

        keyStore.load(null, null);
        keyStore.setKeyEntry(alias, keyPair.getPrivate(), null, new Certificate[] { certificate });

        return keyStore;
    }
}
