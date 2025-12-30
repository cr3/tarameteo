#ifndef CLIENT_H_MOCK
#define CLIENT_H_MOCK

#ifdef UNIT_TEST

#include "Arduino.h"
#include <stdint.h>

// Mock Client class (base class for network clients)
class Client : public Stream {
public:
    virtual ~Client() {}

    virtual int connect(IPAddress ip, uint16_t port) = 0;
    virtual int connect(const char* host, uint16_t port) = 0;
    virtual size_t write(uint8_t) = 0;
    virtual size_t write(const uint8_t* buf, size_t size) = 0;
    virtual int available() = 0;
    virtual int read() = 0;
    virtual int read(uint8_t* buf, size_t size) = 0;
    virtual int peek() = 0;
    virtual void flush() = 0;
    virtual void stop() = 0;
    virtual uint8_t connected() = 0;
    virtual operator bool() = 0;
};

#endif // UNIT_TEST
#endif // CLIENT_H_MOCK
