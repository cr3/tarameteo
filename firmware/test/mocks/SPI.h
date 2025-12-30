#ifndef SPI_H_MOCK
#define SPI_H_MOCK

#ifdef UNIT_TEST

#include "Arduino.h"
#include <stdint.h>

// SPI modes
#define SPI_MODE0 0x00
#define SPI_MODE1 0x01
#define SPI_MODE2 0x02
#define SPI_MODE3 0x03

// BitOrder enum (compatible with Adafruit BusIO)
// Some platforms have this enum, Adafruit expects it
enum BitOrder {
    LSBFIRST = 0,
    MSBFIRST = 1
};

// Mock SPISettings class
class SPISettings {
public:
    SPISettings() {}
    SPISettings(uint32_t clock, uint8_t bitOrder, uint8_t dataMode) {
        (void)clock;
        (void)bitOrder;
        (void)dataMode;
    }
};

// Mock SPIClass
class SPIClass {
public:
    void begin() {}
    void begin(int8_t sck, int8_t miso, int8_t mosi, int8_t ss) {
        (void)sck;
        (void)miso;
        (void)mosi;
        (void)ss;
    }
    void end() {}
    void beginTransaction(SPISettings settings) { (void)settings; }
    void endTransaction() {}
    uint8_t transfer(uint8_t data) {
        (void)data;
        return 0;
    }
    uint16_t transfer16(uint16_t data) {
        (void)data;
        return 0;
    }
    void transfer(void* buf, size_t count) {
        (void)buf;
        (void)count;
    }
    void setBitOrder(uint8_t bitOrder) { (void)bitOrder; }
    void setDataMode(uint8_t dataMode) { (void)dataMode; }
    void setFrequency(uint32_t freq) { (void)freq; }
    void setClockDivider(uint8_t clockDiv) { (void)clockDiv; }
};

extern SPIClass SPI;

#endif // UNIT_TEST
#endif // SPI_H_MOCK
