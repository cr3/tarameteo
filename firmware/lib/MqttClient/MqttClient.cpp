#include "MqttClient.h"

MqttClient::MqttClient(const char* server, int port, bool useTLS,
                       const char* apiKey, const char* sensorName)
    : _server(server),
      _port(port),
      _useTLS(useTLS),
      _apiKey(apiKey),
      _sensorName(sensorName),
      _retryCount(0),
      _mqttClient(useTLS ? _wifiClientSecure : _wifiClient) {

    _lastError[0] = '\0';

    snprintf(_topic, sizeof(_topic), "weather/%s", _sensorName);
    snprintf(_clientId, sizeof(_clientId), "tarameteo-%s", _sensorName);
    snprintf(_lwTopic, sizeof(_lwTopic), "status/%s", _sensorName);
}

bool MqttClient::begin() {
    _mqttClient.setBufferSize(MQTT_BUFFER_SIZE);
    _mqttClient.setServer(_server, _port);

    if (_useTLS) {
	// Skip certificate verification by default
        _wifiClientSecure.setInsecure();
    }

    return true;
}

bool MqttClient::connect() {
    if (_mqttClient.connected()) {
        return true;
    }

    Serial.printf("Connecting to MQTT broker at %s:%d...\n", _server, _port);

    const char* lwMessage = "offline";

    bool connected = _mqttClient.connect(
        _clientId,
        _lwTopic,
        0,  // QoS
        true,  // retain
        lwMessage
    );

    if (!connected) {
        int state = _mqttClient.state();
        switch (state) {
            case -4:
                setError("Connection timeout");
                break;
            case -3:
                setError("Connection lost");
                break;
            case -2:
                setError("Connect failed");
                break;
            case -1:
                setError("Disconnected");
                break;
            case 1:
                setError("Bad protocol");
                break;
            case 2:
                setError("Bad client ID");
                break;
            case 3:
                setError("Unavailable");
                break;
            case 4:
                setError("Bad credentials");
                break;
            case 5:
                setError("Unauthorized");
                break;
            default:
                setError("Unknown error");
                break;
        }
        return false;
    }

    // Publish online status
    _mqttClient.publish(_lwTopic, "online", true);

    Serial.println("Connected to MQTT broker");
    return true;
}

bool MqttClient::isConnected() {
    return _mqttClient.connected();
}

bool MqttClient::publishWeatherData(const WeatherData& data) {
    _retryCount = 0;

    if (!isConnected()) {
        if (!connect()) {
            return false;
        }
    }

    char payload[MQTT_BUFFER_SIZE];
    if (!buildPayload(data, payload, sizeof(payload))) {
        setError("Failed to build JSON payload");
        return false;
    }

    // Publish with retries
    for (_retryCount = 0; _retryCount <= MAX_RETRIES; _retryCount++) {
        if (_retryCount > 0) {
            Serial.printf("Retry attempt %d/%d\n", _retryCount, MAX_RETRIES);
            delay(1000 * _retryCount);
        }

        bool success = _mqttClient.publish(_topic, payload, false);

        if (success) {
            Serial.printf("Published to topic: %s\n", _topic);
            _mqttClient.loop();
            return true;
        }

        if (!isConnected()) {
            Serial.println("Connection lost, attempting to reconnect...");
            if (!connect()) {
                setError("Reconnection failed");
                continue;
            }
        }
    }

    setError("Failed to publish after max retries");
    return false;
}

void MqttClient::disconnect() {
    if (_mqttClient.connected()) {
        _mqttClient.publish(_lwTopic, "offline", true);
        _mqttClient.disconnect();
    }
}

void MqttClient::setCACert(const char* caCert) {
    if (_useTLS) {
        _wifiClientSecure.setCACert(caCert);
    }
}

bool MqttClient::buildPayload(const WeatherData& data, char* buffer, size_t size) {
    StaticJsonDocument<MQTT_BUFFER_SIZE> doc;

    doc["api_key"] = _apiKey;
    doc["timestamp"] = data.timestamp;
    doc["temperature"] = data.temperature;
    doc["humidity"] = data.humidity;
    doc["pressure"] = data.pressure;

    if (data.altitude != 0) {
        doc["altitude"] = data.altitude;
    }

    if (data.rssi != 0) {
        doc["rssi"] = data.rssi;
    }

    if (data.retryCount > 0) {
        doc["retry_count"] = data.retryCount;
    }

    size_t len = serializeJson(doc, buffer, size);
    if (len == 0 || len >= size) {
        return false;
    }

    return true;
}

void MqttClient::setError(const char* error) {
    strncpy(_lastError, error, sizeof(_lastError) - 1);
    _lastError[sizeof(_lastError) - 1] = '\0';
}
