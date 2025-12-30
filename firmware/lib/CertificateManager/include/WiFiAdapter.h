#ifndef WIFI_ADAPTER_H
#define WIFI_ADAPTER_H

#include "IWiFi.h"
#include <WiFi.h>

// Adapter that wraps the real WiFi class
class WiFiAdapter : public IWiFi {
public:
    void disconnect() override {
        WiFi.disconnect();
    }

    void mode(uint8_t mode) override {
        WiFi.mode((wifi_mode_t)mode);
    }

    bool softAPConfig(const IPAddress& local_ip, const IPAddress& gateway, const IPAddress& subnet) override {
        return WiFi.softAPConfig(local_ip, gateway, subnet);
    }

    bool softAP(const char* ssid) override {
        return WiFi.softAP(ssid);
    }

    IPAddress softAPIP() override {
        return WiFi.softAPIP();
    }

    int softAPgetStationNum() override {
        return WiFi.softAPgetStationNum();
    }

    void macAddress(uint8_t* mac) override {
        WiFi.macAddress(mac);
    }
};

#endif // WIFI_ADAPTER_H
