#include "WiFiManager.h"

bool WiFiManager::begin() {
    WiFi.mode(WIFI_STA);
    return true;
}

bool WiFiManager::connect() {
    return attemptConnection();
}

bool WiFiManager::reconnect() {
    if (_reconnectAttempts >= MAX_RECONNECT_ATTEMPTS) {
        updateLastError("Maximum reconnection attempts reached");
        return false;
    }

    _reconnectAttempts++;
    
    // Try to reconnect with exponential backoff
    for (int attempt = 0; attempt < MAX_RECONNECT_ATTEMPTS; attempt++) {
        if (attemptConnection()) {
            _reconnectAttempts = 0;  // Reset counter on successful connection
            return true;
        }
        
        if (attempt < MAX_RECONNECT_ATTEMPTS - 1) {
            delay(RECONNECT_DELAY_MS * (1 << attempt));  // Exponential backoff
        }
    }
    
    snprintf(_lastError, sizeof(_lastError), 
             "Failed to reconnect after %d attempts", _reconnectAttempts);
    return false;
}

bool WiFiManager::attemptConnection() {
    if (WiFi.status() == WL_CONNECTED) {
        return true;  // Already connected
    }
    
    WiFi.disconnect();
    delay(100);  // Short delay to ensure disconnect
    
    WiFi.begin(_ssid, _password);
    
    // Wait for connection with timeout
    unsigned long startTime = millis();
    while (WiFi.status() != WL_CONNECTED) {
        if (millis() - startTime > 10000) {  // 10 second timeout
            updateLastError("Connection timeout");
            return false;
        }
        delay(100);
    }
    
    return true;
}

void WiFiManager::disconnect() {
    WiFi.disconnect();
    _reconnectAttempts = 0;
}

bool WiFiManager::isConnected() const {
    return WiFi.status() == WL_CONNECTED;
}

int WiFiManager::getRSSI() const {
    return WiFi.RSSI();
}

const char* WiFiManager::getIP() const {
    static char ipStr[16];
    IPAddress ip = WiFi.localIP();
    snprintf(ipStr, sizeof(ipStr), "%d.%d.%d.%d", 
             ip[0], ip[1], ip[2], ip[3]);
    return ipStr;
}

void WiFiManager::updateLastError(const char* error) {
    strncpy(_lastError, error, sizeof(_lastError) - 1);
    _lastError[sizeof(_lastError) - 1] = '\0';
} 