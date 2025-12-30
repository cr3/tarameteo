#include "PowerManager.h"
#include <cstring>

PowerManager::PowerManager(unsigned long sleepDurationSeconds) : _sleepDuration(sleepDurationSeconds) {
  _lastError[0] = '\0';
}

bool PowerManager::begin() {
  esp_sleep_enable_timer_wakeup(_sleepDuration * 1000000ULL); // Convert to microseconds
  return true;
}

void PowerManager::prepareForSleep() {
  Serial.println("Preparing for deep sleep...");
  // Add any cleanup needed before sleep
  // For example: close files, disconnect peripherals, etc.
}

void PowerManager::sleep() {
  prepareForSleep();
  Serial.println("Entering deep sleep...");
  esp_deep_sleep_start();
}

void PowerManager::updateLastError(const char *error) {
  strncpy(_lastError, error, sizeof(_lastError) - 1);
  _lastError[sizeof(_lastError) - 1] = '\0';
}