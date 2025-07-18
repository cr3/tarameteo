#ifndef WIFI_MANAGER_H
#define WIFI_MANAGER_H

#include <WiFi.h>

class WiFiManager {
public:
    static constexpr int MAX_RECONNECT_ATTEMPTS = 3;
    static constexpr int RECONNECT_DELAY_MS = 1000;  // 1 second between attempts
    
    WiFiManager(const char* ssid, const char* password) : _reconnectAttempts(0) {
        _lastError[0] = '\0';
        strncpy(_ssid, ssid, sizeof(_ssid) - 1);
        _ssid[sizeof(_ssid) - 1] = '\0';
        strncpy(_password, password, sizeof(_password) - 1);
        _password[sizeof(_password) - 1] = '\0';
    }
    
    bool begin();
    bool connect();  // Uses stored credentials
    bool reconnect();  // Uses stored credentials
    void disconnect();
    bool isConnected() const;
    int getRSSI() const;
    const char* getIP() const;
    const char* getLastError() const { return _lastError; }
    int getReconnectAttempts() const { return _reconnectAttempts; }
    void resetReconnectAttempts() { _reconnectAttempts = 0; }

private:
    char _ssid[32];
    char _password[64];
    char _lastError[128];
    int _reconnectAttempts;
    
    void updateLastError(const char* error);
    bool attemptConnection();
};

#endif 