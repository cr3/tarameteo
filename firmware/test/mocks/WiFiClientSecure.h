#ifndef WIFI_CLIENT_SECURE_H_MOCK
#define WIFI_CLIENT_SECURE_H_MOCK

#ifdef UNIT_TEST

#include "WiFiClient.h"

// Mock WiFiClientSecure class (TLS/SSL client)
class WiFiClientSecure : public WiFiClient {
public:
    WiFiClientSecure() {}
    ~WiFiClientSecure() {}

    // Certificate management
    void setCACert(const char* rootCA) { (void)rootCA; }
    void setCertificate(const char* clientCert) { (void)clientCert; }
    void setPrivateKey(const char* privateKey) { (void)privateKey; }
    void setInsecure() {}

    // Load certificates from memory
    bool loadCACert(const char* caCertificate, size_t length) {
        (void)caCertificate;
        (void)length;
        return true;
    }

    bool loadCertificate(const char* clientCertificate, size_t length) {
        (void)clientCertificate;
        (void)length;
        return true;
    }

    bool loadPrivateKey(const char* privateKey, size_t length) {
        (void)privateKey;
        (void)length;
        return true;
    }

    // Verification
    bool verify(const char* fingerprint, const char* domain) {
        (void)fingerprint;
        (void)domain;
        return true;
    }

    void setHandshakeTimeout(unsigned long timeout) { (void)timeout; }
};

#endif // UNIT_TEST
#endif // WIFI_CLIENT_SECURE_H_MOCK
