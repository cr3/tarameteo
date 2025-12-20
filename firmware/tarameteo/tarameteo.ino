/*
 * TaraMeteo Firmware
 * Weather station using XIAO_ESP32S3 and BME280 sensor
 *
 * Features:
 * - Deep sleep power management
 * - WiFi connectivity with auto-reconnect
 * - Secure MQTTS (MQTT over TLS) support
 * - Sensor data validation
 * - NTP time synchronization for accurate timestamps
 * - Last Will and Testament for offline detection
 */

#include <esp_sleep.h>
#include "config.h"
#include "BME280Sensor.h"
#include "WiFiManager.h"
#include "MqttClient.h"
#include "PowerManager.h"
#include "TimeManager.h"

BME280Sensor sensor(BME280_ADDRESS, BME280_SDA, BME280_SCL, SEA_LEVEL_PRESSURE);
WiFiManager wifiManager(WIFI_SSID, WIFI_PASSWORD);
MqttClient mqttClient(MQTT_SERVER, MQTT_PORT, MQTT_USE_TLS, API_KEY, SENSOR_NAME);
PowerManager powerManager(SLEEP_DURATION);
TimeManager timeManager(NTP_TIMEOUT_MS, NTP_SYNC_INTERVAL_MS);

void printStatus(const char* component, bool success, const char* error = nullptr) {
    Serial.print(component);
    Serial.print(": ");
    Serial.println(success ? "OK" : "FAILED");
    if (!success && error) {
        Serial.print("  Error: ");
        Serial.println(error);
    }
}

void setup() {
    Serial.begin(115200);
    delay(1000);  // Give serial connection time to start

    Serial.println("\n=== TaraMeteo Weather Station ===");
    Serial.printf("Sensor: %s\n", SENSOR_NAME);
    Serial.println("Initializing components...");

    // Initialize sensor
    if (!sensor.begin()) {
        printStatus("BME280 Sensor", false, sensor.getLastError());
        powerManager.sleep();
    }
    printStatus("BME280 Sensor", true);

    // Initialize WiFi
    if (!wifiManager.begin()) {
        printStatus("WiFi Manager", false, wifiManager.getLastError());
        powerManager.sleep();
    }
    printStatus("WiFi Manager", true);

    // Connect to WiFi
    Serial.println("Connecting to WiFi...");
    if (!wifiManager.connect()) {
        printStatus("WiFi Connection", false, wifiManager.getLastError());
        powerManager.sleep();
    }
    printStatus("WiFi Connection", true);
    Serial.printf("Connected to %s (IP: %s)\n", WIFI_SSID, wifiManager.getIP());
    Serial.printf("WiFi RSSI: %d dBm\n", wifiManager.getRSSI());

    // Initialize time manager
    if (!timeManager.begin()) {
        printStatus("Time Manager", false, timeManager.getLastError());
        powerManager.sleep();
    }
    printStatus("Time Manager", true);

    // Sync time with NTP servers
    Serial.println("Synchronizing time with NTP servers...");
    if (!timeManager.syncTime()) {
        printStatus("Time Sync", false, timeManager.getLastError());
        Serial.println("Warning: Using device uptime for timestamps");
    } else {
        printStatus("Time Sync", true);
        Serial.printf("Current timestamp: %lu\n", timeManager.getCurrentTimestamp());

        // Display formatted time
        char timeString[32];
        if (timeManager.getFormattedTime(timeString, sizeof(timeString))) {
            Serial.printf("Current time: %s\n", timeString);
        }
    }

    // Initialize MQTT client
    if (!mqttClient.begin()) {
        printStatus("MQTT Client", false, mqttClient.getLastError());
        powerManager.sleep();
    }
    printStatus("MQTT Client", true);

    // Set CA certificate for TLS if configured
#ifdef MQTT_CA_CERT
    mqttClient.setCACert(MQTT_CA_CERT);
#endif

    // Connect to MQTT broker
    Serial.println("Connecting to MQTT broker...");
    if (!mqttClient.connect()) {
        printStatus("MQTT Connection", false, mqttClient.getLastError());
        // Continue anyway - will retry in loop
    } else {
        printStatus("MQTT Connection", true);
        Serial.printf("Connected to %s:%d\n", MQTT_SERVER, MQTT_PORT);
    }

    // Initialize power management
    if (!powerManager.begin()) {
        printStatus("Power Manager", false, powerManager.getLastError());
        powerManager.sleep();
    }
    printStatus("Power Manager", true);

    Serial.println("All components initialized successfully");
    Serial.printf("Sleep duration: %d seconds (%.1f minutes)\n",
                 SLEEP_DURATION, SLEEP_DURATION / 60.0);
    Serial.println("Starting main loop...\n");
}

void loop() {
    // Check sensor availability
    if (!sensor.isAvailable()) {
        printStatus("Sensor Check", false, sensor.getLastError());
        powerManager.sleep();
    }

    // Check WiFi connection
    if (!wifiManager.isConnected()) {
        Serial.println("WiFi disconnected, attempting to reconnect...");
        if (!wifiManager.reconnect()) {
            printStatus("WiFi Reconnect", false, wifiManager.getLastError());
            Serial.printf("Reconnect attempts: %d/%d\n",
                         wifiManager.getReconnectAttempts(),
                         WiFiManager::MAX_RECONNECT_ATTEMPTS);
            powerManager.sleep();
        }
        printStatus("WiFi Reconnect", true);
        Serial.printf("Reconnected to %s (IP: %s)\n",
                     WIFI_SSID, wifiManager.getIP());
    }

    // Read sensor data
    WeatherData data = {
        sensor.getTemperature(),
        sensor.getPressure(),
        sensor.getHumidity(),
        sensor.getAltitude(),
        wifiManager.getRSSI(),
        timeManager.getCurrentTimestamp(),
        0  // retryCount will be updated by MQTT client
    };

    // Print sensor readings
    Serial.println("Sensor Readings:");
    Serial.printf("Temperature: %.1f°C\n", data.temperature);
    Serial.printf("Pressure: %.1f hPa\n", data.pressure);
    Serial.printf("Humidity: %.1f%%\n", data.humidity);
    Serial.printf("Altitude: %.1f m\n", data.altitude);
    Serial.printf("WiFi RSSI: %d dBm\n", data.rssi);
    Serial.printf("Timestamp: %lu\n", data.timestamp);

    // Display formatted time if available
    if (timeManager.isTimeSynced()) {
        char timeString[32];
        if (timeManager.getFormattedTime(timeString, sizeof(timeString))) {
            Serial.printf("Time: %s\n", timeString);
        }
    }

    // Publish data to MQTT broker
    Serial.println("\nPublishing data to MQTT broker...");
    if (!mqttClient.publishWeatherData(data)) {
        printStatus("Data Publish", false, mqttClient.getLastError());
        Serial.printf("Retry count: %d/%d\n",
                     mqttClient.getRetryCount(),
                     MqttClient::MAX_RETRIES);

        // Store retry count for next attempt
        data.retryCount = mqttClient.getRetryCount();
    } else {
        printStatus("Data Publish", true);
        Serial.printf("Data published successfully to topic: weather/%s\n", SENSOR_NAME);
    }

    // Disconnect from MQTT (reduces power consumption during sleep)
    mqttClient.disconnect();

    // Enter deep sleep regardless of publish status
    Serial.printf("Entering deep sleep for %d seconds...\n", SLEEP_DURATION);
    Serial.println("=====================================\n");
    powerManager.sleep();
}
