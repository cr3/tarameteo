/*
 * TaraMeteo Firmware
 * Weather station using XIAO_ESP32S3 and BME280 sensor
 * Features:
 * - Deep sleep power management
 * - WiFi connectivity with auto-reconnect
 * - Secure HTTPS data transmission
 * - Sensor data validation
 */

#include <esp_sleep.h>
#include "config.h"
#include "BME280Sensor.h"
#include "WiFiManager.h"
#include "HttpClient.h"
#include "PowerManager.h"

BME280Sensor sensor(BME280_ADDRESS, BME280_SDA, BME280_SCL, SEA_LEVEL_PRESSURE);
WiFiManager wifiManager(WIFI_SSID, WIFI_PASSWORD);
HttpClient httpClient(HTTP_SERVER, HTTP_PORT, HTTP_USE_HTTPS, API_KEY);
PowerManager powerManager(SLEEP_DURATION);

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
    if (!wifiManager.connect()) {
        printStatus("WiFi Connection", false, wifiManager.getLastError());
        powerManager.sleep();
    }
    printStatus("WiFi Connection", true);
    Serial.printf("Connected to %s (IP: %s)\n", WIFI_SSID, wifiManager.getIP());
    
    // Initialize HTTP client
    if (!httpClient.begin()) {
        printStatus("HTTP Client", false, httpClient.getLastError());
        powerManager.sleep();
    }
    printStatus("HTTP Client", true);
    
    // Initialize power management
    if (!powerManager.begin()) {
        printStatus("Power Manager", false, powerManager.getLastError());
        powerManager.sleep();
    }
    printStatus("Power Manager", true);
    
    Serial.println("All components initialized successfully");
    Serial.print("Sleep duration: ");
    Serial.print(SLEEP_DURATION);
    Serial.println(" seconds");
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
        wifiManager.getRSSI()
    };
    
    // Print sensor readings
    Serial.println("Sensor Readings:");
    Serial.printf("Temperature: %.1f°C\n", data.temperature);
    Serial.printf("Pressure: %.1f hPa\n", data.pressure);
    Serial.printf("Humidity: %.1f%%\n", data.humidity);
    Serial.printf("Altitude: %.1f m\n", data.altitude);
    Serial.printf("WiFi RSSI: %d dBm\n", data.rssi);
    
    // Post data to server
    Serial.println("\nPosting data to server...");
    if (!httpClient.postWeatherData(data)) {
        printStatus("Data Post", false, httpClient.getLastError());
        Serial.printf("Retry count: %d/%d\n", 
                     httpClient.getRetryCount(), 
                     HttpClient::MAX_RETRIES);
    } else {
        printStatus("Data Post", true);
    }
    
    // Enter deep sleep regardless of post status
    Serial.println("Entering deep sleep...\n");
    powerManager.sleep();
}
