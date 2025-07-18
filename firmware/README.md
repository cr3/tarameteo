# TaraMeteo

Arduino-based temperature monitoring system.

## Setup

1. Install the ESP32 core libraries:
   ```bash
   arduino-cli core install esp32:esp32
   ```

2. Copy the example configuration file:
   ```bash
   cp tarameteo/config.h.example tarameteo/config.h
   ```

3. Edit `tarameteo/config.h` with your settings:
   - Set your WiFi credentials (`WIFI_SSID` and `WIFI_PASSWORD`)
   - Set your API endpoint (`API_URL`)
   - Adjust other settings if necessary.

## Build and Upload

```bash
cmake --build build --target upload
```
