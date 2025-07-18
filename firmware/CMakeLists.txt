cmake_minimum_required(VERSION 3.14)
project(TaraMeteo)

include(cmake/Arduino.cmake)

set(ARDUINO_FQBN "esp32:esp32:XIAO_ESP32C3")
set(ARDUINO_PORT "/dev/ttyACM0")
set(ARDUINO_BAUDRATE "115200")

add_arduino_upload_target(upload tarameteo ${ARDUINO_FQBN} ${ARDUINO_PORT})
add_arduino_monitor_target(monitor ${ARDUINO_PORT} ${ARDUINO_BAUDRATE})
