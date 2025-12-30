#ifndef WIRE_H_MOCK
#define WIRE_H_MOCK

#ifdef UNIT_TEST

#include <stdint.h>
#include <stddef.h>

// Mock TwoWire class for I2C communication
class TwoWire {
public:
    void begin() {}
    void begin(int sda, int scl) { (void)sda; (void)scl; }
    void beginTransmission(uint8_t address) { (void)address; }
    uint8_t endTransmission() { return 0; }
    uint8_t requestFrom(uint8_t address, size_t quantity) {
        (void)address; (void)quantity;
        return 0;
    }
    size_t write(uint8_t data) { (void)data; return 1; }
    int read() { return -1; }
    int available() { return 0; }
    void setClock(uint32_t frequency) { (void)frequency; }
};

extern TwoWire Wire;

#endif // UNIT_TEST
#endif // WIRE_H_MOCK
