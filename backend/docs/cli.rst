# Sample Data Generation Script

This script generates realistic weather data for testing the TaraMeteo API.

## Features

- Generates realistic weather data with diurnal variations
- Creates sensors automatically if they don't exist
- Supports configurable intervals and durations
- Includes trend variations for more realistic data
- Supports both command-line arguments and configuration files
- **NEW**: Supports firmware-compatible payload format with Unix timestamps
- **NEW**: Includes altitude, RSSI, and retry count data
- **NEW**: Configurable weather parameter ranges

## Installation

Make sure you have the required dependencies:

```bash
pip install httpx attrs
```

## Usage

### Basic Usage

Generate data for a new sensor (will create the sensor automatically):

```bash
python generate_sample_data.py --sensor-name "my-sensor"
```

### With API Key

If you already have a sensor and API key:

```bash
python generate_sample_data.py --sensor-name "my-sensor" --api-key "your-api-key-here"
```

### Using Configuration File

Create a config file (see `sample_config.json` for an example):

```bash
python generate_sample_data.py --config sample_config.json
```

### Advanced Options

```bash
python generate_sample_data.py \
    --sensor-name "outdoor-sensor" \
    --api-key "your-api-key" \
    --interval 30 \
    --duration 48 \
    --start-time "2024-01-01 06:00:00"
```

## Command Line Options

- `--api-url`: API base URL (default: http://localhost:8000/api)
- `--sensor-name`: Name of the sensor (required)
- `--api-key`: API key for the sensor (optional, will create sensor if not provided)
- `--interval`: Interval between data points in seconds (default: 60)
- `--duration`: Duration in hours (default: 24)
- `--start-time`: Start time in format YYYY-MM-DD HH:MM:SS or YYYY-MM-DD
- `--config`: Path to JSON configuration file
- `--unix-timestamp`: Use Unix timestamps (matches firmware format)
- `--base-altitude`: Base altitude in meters (default: 100.0)
- `--base-rssi`: Base RSSI in dBm (default: -50)

## Configuration File Format

```json
{
    "api-url": "http://localhost:8000/api",
    "sensor-name": "test-sensor-01",
    "api-key": "",
    "interval": 60,
    "duration": 24,
    "start-time": "2024-01-01 00:00:00",
    "weather": {
        "base-temperature": 20.0,
        "base-humidity": 60.0,
        "base-pressure": 1013.25,
        "base-altitude": 100.0,
        "base-rssi": -50,
        "temperature-variation": 5.0,
        "humidity-variation": 20.0,
        "pressure-variation": 10.0,
        "altitude-variation": 5.0,
        "rssi-variation": 15,
        "trend-duration-hours": 6,
        "use-unix-timestamp": true
    }
}
```

## Data Generation

The script generates realistic weather data with the following characteristics:

- **Temperature**: Varies throughout the day (warmer in afternoon, cooler at night)
- **Humidity**: Inversely related to temperature  
- **Pressure**: Smaller variations with realistic atmospheric pressure values
- **Altitude**: Slight variations due to barometric changes
- **RSSI**: WiFi signal strength variations (-100 to -20 dBm range)
- **Retry Count**: Occasionally simulates network retry scenarios (5% chance)
- **Trends**: Long-term trends that change every 6 hours
- **Variations**: Random variations within realistic bounds
- **Timestamp Format**: Supports both ISO format and Unix timestamps (firmware compatible)

## Examples

### Generate 1 hour of data every 30 seconds

```bash
python generate_sample_data.py \
    --sensor-name "quick-test" \
    --interval 30 \
    --duration 1
```

### Generate data for a specific time period

```bash
python generate_sample_data.py \
    --sensor-name "historical-data" \
    --start-time "2024-01-01 00:00:00" \
    --duration 168  # 1 week
```

### Use with different API server

```bash
python generate_sample_data.py \
    --api-url "https://api.tarameteo.com/api" \
    --sensor-name "production-sensor" \
    --api-key "your-production-api-key"
```

### Generate firmware-compatible data

```bash
python generate_sample_data.py \
    --sensor-name "esp32-outdoor" \
    --unix-timestamp \
    --base-altitude 250.5 \
    --base-rssi -65
```

### Generate data with custom weather parameters

```bash
python generate_sample_data.py \
    --sensor-name "mountain-station" \
    --config custom_mountain_config.json
```

## Output

The script will output:

1. Sensor creation status (if creating a new sensor)
2. API key for new sensors
3. Real-time data transmission status
4. Error messages if any issues occur

Example output:
```
Creating sensor 'test-sensor-01'...
Created sensor with API key: abc123def456...
Generating weather data for sensor 'test-sensor-01'
Duration: 24 hours
Interval: 60 seconds
Start time: 2024-01-01T00:00:00+00:00
--------------------------------------------------
Sent data: 2024-01-01 00:00:00 - T: 18.5°C, H: 65.2%, P: 1012.8 hPa, Alt: 98.3m, RSSI: -52 dBm, Retry: 0
Sent data: 2024-01-01 00:01:00 - T: 18.3°C, H: 66.1%, P: 1013.1 hPa, Alt: 99.1m, RSSI: -48 dBm, Retry: 0
...
--------------------------------------------------
Data generation completed
```

## Stopping the Script

Press `Ctrl+C` to stop the script at any time. The script will cleanly exit and show a "Stopped by user" message. 