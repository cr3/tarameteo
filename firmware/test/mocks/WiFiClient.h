#ifndef WIFI_CLIENT_H_MOCK
#define WIFI_CLIENT_H_MOCK

#ifdef UNIT_TEST

#include "Client.h"
#include <stdint.h>

// Mock WiFiClient class
class WiFiClient : public Client {
public:
    WiFiClient() {}

    int connect(const char* host, uint16_t port) {
        (void)host; (void)port;
        return 1;
    }
    int connect(IPAddress ip, uint16_t port) {
        (void)ip; (void)port;
        return 1;
    }

    size_t write(uint8_t byte) override { (void)byte; return 1; }
    size_t write(const uint8_t* buf, size_t size) override {
        (void)buf; (void)size;
        return size;
    }

    int available() override { return 0; }
    int read() override { return -1; }
    int read(uint8_t* buf, size_t size) {
        (void)buf; (void)size;
        return -1;
    }
    int peek() override { return -1; }
    void flush() override {}

    void stop() {}
    uint8_t connected() { return 0; }
    operator bool() { return false; }

    IPAddress remoteIP() { return IPAddress(0, 0, 0, 0); }
    uint16_t remotePort() { return 0; }
    IPAddress localIP() { return IPAddress(0, 0, 0, 0); }
    uint16_t localPort() { return 0; }
};

#endif // UNIT_TEST
#endif // WIFI_CLIENT_H_MOCK
