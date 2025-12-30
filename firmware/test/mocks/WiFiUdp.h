#ifndef WIFI_UDP_H_MOCK
#define WIFI_UDP_H_MOCK

#ifdef UNIT_TEST

#include "Arduino.h"
#include <stdint.h>

// Mock WiFiUDP class
class WiFiUDP : public Stream {
public:
    WiFiUDP() {}

    uint8_t begin(uint16_t port) { (void)port; return 1; }
    void stop() {}

    int beginPacket(const char* host, uint16_t port) {
        (void)host; (void)port;
        return 1;
    }
    int beginPacket(IPAddress ip, uint16_t port) {
        (void)ip; (void)port;
        return 1;
    }

    int endPacket() { return 1; }

    size_t write(uint8_t byte) override { (void)byte; return 1; }
    size_t write(const uint8_t* buffer, size_t size) override {
        (void)buffer; (void)size;
        return size;
    }

    int parsePacket() { return 0; }
    int available() override { return 0; }
    int read() override { return -1; }
    int peek() override { return -1; }
    void flush() {}

    IPAddress remoteIP() { return IPAddress(0, 0, 0, 0); }
    uint16_t remotePort() { return 0; }
};

#endif // UNIT_TEST
#endif // WIFI_UDP_H_MOCK
