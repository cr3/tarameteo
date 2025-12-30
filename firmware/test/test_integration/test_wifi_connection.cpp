/**
 * Integration Test - WiFi Connection
 *
 * This test runs on actual ESP32 hardware and verifies:
 * - WiFi connection works
 * - NVS storage/retrieval works
 * - Real hardware APIs function correctly
 *
 * To run: pio test -e esp32 -f test_integration
 */

#include <Arduino.h>
#include <Preferences.h>
#include <WiFi.h>
#include <unity.h>

// Test credentials (update with your network)
#define TEST_WIFI_SSID "YourTestNetwork"
#define TEST_WIFI_PASSWORD "YourTestPassword"

Preferences prefs;

void setUp(void) {
  // Runs before each test
  Serial.begin(115200);
  delay(100);
}

void tearDown(void) {
  // Runs after each test
  WiFi.disconnect();
  delay(100);
}

void test_wifi_can_connect(void) {
  Serial.println("\n=== Testing WiFi Connection ===");

  WiFi.mode(WIFI_STA);
  WiFi.begin(TEST_WIFI_SSID, TEST_WIFI_PASSWORD);

  // Wait for connection with timeout
  unsigned long start = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - start < 10000) {
    delay(100);
    Serial.print(".");
  }
  Serial.println();

  TEST_ASSERT_EQUAL(WL_CONNECTED, WiFi.status());

  IPAddress ip = WiFi.localIP();
  Serial.printf("Connected! IP: %s\n", ip.toString().c_str());
  Serial.printf("RSSI: %d dBm\n", WiFi.RSSI());

  TEST_ASSERT_NOT_EQUAL(0, ip[0]); // Verify we got an IP
}

void test_nvs_can_store_and_retrieve(void) {
  Serial.println("\n=== Testing NVS Storage ===");

  // Open NVS
  bool opened = prefs.begin("test_nvs", false);
  TEST_ASSERT_TRUE(opened);

  // Store data
  const char *test_string = "test_value_12345";
  size_t written = prefs.putString("test_key", test_string);
  TEST_ASSERT_GREATER_THAN(0, written);

  // Retrieve data
  char buffer[64];
  size_t read = prefs.getString("test_key", buffer, sizeof(buffer));
  TEST_ASSERT_GREATER_THAN(0, read);
  TEST_ASSERT_EQUAL_STRING(test_string, buffer);

  Serial.printf("Stored: %s\n", test_string);
  Serial.printf("Retrieved: %s\n", buffer);

  // Clean up
  prefs.clear();
  prefs.end();
}

void test_wifi_rssi_reading(void) {
  Serial.println("\n=== Testing WiFi RSSI ===");

  // Ensure connected
  if (WiFi.status() != WL_CONNECTED) {
    WiFi.begin(TEST_WIFI_SSID, TEST_WIFI_PASSWORD);
    unsigned long start = millis();
    while (WiFi.status() != WL_CONNECTED && millis() - start < 10000) {
      delay(100);
    }
  }

  TEST_ASSERT_EQUAL(WL_CONNECTED, WiFi.status());

  int rssi = WiFi.RSSI();
  Serial.printf("RSSI: %d dBm\n", rssi);

  // RSSI should be negative (signal strength)
  TEST_ASSERT_LESS_THAN(0, rssi);
  // RSSI should be reasonable (-100 to -30 dBm typical range)
  TEST_ASSERT_GREATER_THAN(-100, rssi);
}

void test_free_heap_sufficient(void) {
  Serial.println("\n=== Testing Heap Memory ===");

  size_t free_heap = ESP.getFreeHeap();
  Serial.printf("Free heap: %u bytes\n", free_heap);

  // Should have at least 50KB free
  TEST_ASSERT_GREATER_THAN(50000, free_heap);
}

// ========================================
// Setup and Loop for PlatformIO
// ========================================

void setup() {
  delay(2000); // Wait for serial monitor

  UNITY_BEGIN();

  RUN_TEST(test_free_heap_sufficient);
  RUN_TEST(test_nvs_can_store_and_retrieve);
  RUN_TEST(test_wifi_can_connect);
  RUN_TEST(test_wifi_rssi_reading);

  UNITY_END();
}

void loop() {
  // Tests run once in setup()
  delay(1000);
}
