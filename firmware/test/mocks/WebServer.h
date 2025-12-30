#ifndef WEB_SERVER_H_MOCK
#define WEB_SERVER_H_MOCK

#ifdef UNIT_TEST

#include "Arduino.h"
#include "WiFiClient.h"
#include <stdint.h>
#include <functional>

// HTTP methods (exported globally for compatibility)
enum HTTPMethod {
    HTTP_GET = 0,
    HTTP_POST,
    HTTP_PUT,
    HTTP_PATCH,
    HTTP_DELETE,
    HTTP_OPTIONS
};

// Mock WebServer class
class WebServer {
public:
    WebServer(uint16_t port = 80) { (void)port; }
    ~WebServer() {}

    void begin() {}
    void begin(uint16_t port) { (void)port; }
    void handleClient() {}
    void close() {}
    void stop() {}

    // Request handlers
    void on(const char* uri, std::function<void()> handler) {
        (void)uri;
        (void)handler;
    }

    void on(const char* uri, HTTPMethod method, std::function<void()> handler) {
        (void)uri;
        (void)method;
        (void)handler;
    }

    void onNotFound(std::function<void()> fn) { (void)fn; }

    // Request information
    String uri() { return String(""); }
    HTTPMethod method() { return HTTP_GET; }
    String arg(const char* name) { (void)name; return String(""); }
    String arg(int i) { (void)i; return String(""); }
    String argName(int i) { (void)i; return String(""); }
    int args() { return 0; }
    bool hasArg(const char* name) { (void)name; return false; }

    // Response methods
    void send(int code, const char* content_type = nullptr, const String& content = String("")) {
        (void)code;
        (void)content_type;
        (void)content;
    }

    void send(int code, const char* content_type, const char* content) {
        (void)code;
        (void)content_type;
        (void)content;
    }

    void sendHeader(const char* name, const char* value, bool first = false) {
        (void)name;
        (void)value;
        (void)first;
    }

    void setContentLength(size_t len) { (void)len; }

    // Client access
    WiFiClient client() { return WiFiClient(); }
};

#endif // UNIT_TEST
#endif // WEB_SERVER_H_MOCK
