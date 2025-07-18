#ifndef HTTP_CLIENT_H
#define HTTP_CLIENT_H

#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <WiFiClientSecure.h>

struct WeatherData {
    float temperature;
    float pressure;
    float humidity;
    float altitude;
    int rssi;
};

class HttpClient {
public:
    static constexpr size_t JSON_BUFFER_SIZE = 512;
    static constexpr int MAX_RETRIES = 3;
    static constexpr int RETRY_DELAY_MS = 5000;  // 5 seconds between retries

    // Constructor takes server details and API key
    HttpClient(const char* server, 
              int port = 443, 
              bool useHttps = true,
              const char* apiKey = nullptr);
              
    bool begin();
    bool postWeatherData(const WeatherData& data);
    const char* getLastError() const { return _lastError; }
    int getRetryCount() const { return _retryCount; }
    void resetRetryCount() { _retryCount = 0; }

private:
    HTTPClient _http;
    WiFiClientSecure _wifiClient;
    const char* _server;
    int _port;
    bool _useHttps;
    char _apiKey[64];
    char _lastError[128];
    int _retryCount;
    bool _hasApiKey;

    void updateLastError(const char* error);
    bool createJsonPayload(const WeatherData& data, char* buffer, size_t size);
    bool setupSecureConnection();
    void addAuthHeaders();
    bool retryPost(const WeatherData& data);
    String buildUrl() const;
    bool isRetryableError(int httpCode) const;
};

#endif 