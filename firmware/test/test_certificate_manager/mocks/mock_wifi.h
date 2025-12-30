#ifndef MOCK_WIFI_H
#define MOCK_WIFI_H

#include "Arduino.h"
#include "../../../lib/CertificateManager/include/IWiFi.h"
#include <stdint.h>
#include <string.h>

class MockWiFi : public IWiFi {
public:
    MockWiFi() : disconnectCalled(false), apMode(false), apConfigured(false),
                 apStarted(false), stationCount(0) {
        mac[0] = 0xAA;
        mac[1] = 0xBB;
        mac[2] = 0xCC;
        mac[3] = 0xDD;
        mac[4] = 0xEE;
        mac[5] = 0xFF;
        apIP = IPAddress(192, 168, 4, 1);
    }

    void disconnect() override {
        disconnectCalled = true;
    }

    void mode(uint8_t mode) override {
        apMode = (mode == 2); // WIFI_AP = 2
    }

    bool softAPConfig(const IPAddress& local_ip, const IPAddress& gateway, const IPAddress& subnet) override {
        apConfigured = true;
        apIP = local_ip;
        return true;
    }

    bool softAP(const char* ssid) override {
        if (ssid) {
            apSSID = String(ssid);
            apStarted = true;
            return true;
        }
        return false;
    }

    IPAddress softAPIP() override {
        return apIP;
    }

    int softAPgetStationNum() override {
        return stationCount;
    }

    void macAddress(uint8_t* macOut) override {
        if (macOut) {
            memcpy(macOut, mac, 6);
        }
    }

    // Test helpers
    void setStationCount(int count) {
        stationCount = count;
    }

    void reset() {
        disconnectCalled = false;
        apMode = false;
        apConfigured = false;
        apStarted = false;
        stationCount = 0;
        apSSID = String();
    }

    bool disconnectCalled;
    bool apMode;
    bool apConfigured;
    bool apStarted;
    String apSSID;
    int stationCount;
    IPAddress apIP;
    uint8_t mac[6];
};

#endif // MOCK_WIFI_H
