#include "HttpClient.h"

HttpClient::HttpClient(const char* server, int port, bool useHttps, const char* apiKey) 
    : _server(server), _port(port), _useHttps(useHttps), 
      _retryCount(0), _hasApiKey(false) {
    _lastError[0] = '\0';
    _apiKey[0] = '\0';
    
    if (apiKey) {
        strncpy(_apiKey, apiKey, sizeof(_apiKey) - 1);
        _apiKey[sizeof(_apiKey) - 1] = '\0';
        _hasApiKey = true;
    }
}

bool HttpClient::begin() {
    if (_useHttps) {
        return setupSecureConnection();
    }
    return true;
}

bool HttpClient::setupSecureConnection() {
    _wifiClient.setInsecure();  // Skip certificate validation
    return true;
}

void HttpClient::addAuthHeaders() {
    if (_hasApiKey) {
        _http.addHeader("X-API-Key", _apiKey);
    }
}

String HttpClient::buildUrl() const {
    String url = String(_useHttps ? "https://" : "http://") + _server;
    if ((_useHttps && _port != 443) || (!_useHttps && _port != 80)) {
        url += ":" + String(_port);
    }
    url += "/api/weather";
    return url;
}

bool HttpClient::isRetryableError(int httpCode) const {
    // Retry on server errors (5xx) and some client errors (4xx)
    return (httpCode >= 500) || 
           (httpCode == 408) || // Request Timeout
           (httpCode == 429) || // Too Many Requests
           (httpCode == 503);   // Service Unavailable
}

bool HttpClient::retryPost(const WeatherData& data) {
    if (_retryCount >= MAX_RETRIES) {
        updateLastError("Max retries exceeded");
        return false;
    }

    _retryCount++;
    delay(RETRY_DELAY_MS);
    return postWeatherData(data);
}

bool HttpClient::createJsonPayload(const WeatherData& data, char* buffer, size_t size) {
    StaticJsonDocument<JSON_BUFFER_SIZE> doc;
    
    doc["temperature"] = round(data.temperature * 10.0f) / 10.0f;  // Round to 1 decimal
    doc["pressure"] = round(data.pressure * 10.0f) / 10.0f;
    doc["humidity"] = round(data.humidity * 10.0f) / 10.0f;
    doc["altitude"] = round(data.altitude * 10.0f) / 10.0f;
    doc["rssi"] = data.rssi;
    doc["timestamp"] = data.timestamp;  // Use the timestamp from WeatherData
    doc["retry_count"] = _retryCount;
    
    return serializeJson(doc, buffer, size) > 0;
}

bool HttpClient::postWeatherData(const WeatherData& data) {
    char jsonBuffer[JSON_BUFFER_SIZE];
    if (!createJsonPayload(data, jsonBuffer, sizeof(jsonBuffer))) {
        updateLastError("Failed to create JSON payload");
        return false;
    }
    
    String url = buildUrl();
    if (_useHttps) {
        _http.begin(_wifiClient, url);
    } else {
        _http.begin(url);
    }
    
    _http.addHeader("Content-Type", "application/json");
    addAuthHeaders();
    
    int httpCode = _http.POST(jsonBuffer);
    bool success = (httpCode == HTTP_CODE_OK || httpCode == HTTP_CODE_CREATED);
    
    if (!success) {
        snprintf(_lastError, sizeof(_lastError), 
                "HTTP POST failed with code %d: %s", 
                httpCode, _http.errorToString(httpCode).c_str());
        
        if (isRetryableError(httpCode)) {
            _http.end();
            return retryPost(data);
        }
    }
    
    _http.end();
    return success;
}

void HttpClient::updateLastError(const char* error) {
    strncpy(_lastError, error, sizeof(_lastError) - 1);
    _lastError[sizeof(_lastError) - 1] = '\0';
} 