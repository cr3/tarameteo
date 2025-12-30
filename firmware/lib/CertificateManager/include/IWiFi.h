#ifndef I_WIFI_H
#define I_WIFI_H

#include <cstdint>

class IPAddress;
class String;

class IWiFi {
public:
  virtual ~IWiFi() = default;
  virtual void disconnect() = 0;
  virtual void mode(uint8_t mode) = 0;
  virtual auto softAPConfig(const IPAddress &local_ip, const IPAddress &gateway, const IPAddress &subnet) -> bool = 0;
  virtual auto softAP(const char *ssid) -> bool = 0;
  virtual auto softAPIP() -> IPAddress = 0;
  virtual auto softAPgetStationNum() -> int = 0;
  virtual void macAddress(uint8_t *mac) = 0;
};

#endif // I_WIFI_H
