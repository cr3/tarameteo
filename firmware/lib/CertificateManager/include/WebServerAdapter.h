#ifndef WEB_SERVER_ADAPTER_H
#define WEB_SERVER_ADAPTER_H

#include "IWebServer.h"
#include <WebServer.h>
#include <functional>

// Adapter that wraps the real WebServer
class WebServerAdapter : public IWebServer {
public:
    WebServerAdapter(int port) : _server(port) {}

    void on(const char* uri, std::function<void()> handler) override {
        _server.on(uri, HTTP_GET, handler);
    }

    void onNotFound(std::function<void()> handler) override {
        _server.onNotFound(handler);
    }

    void begin() override {
        _server.begin();
    }

    void stop() override {
        _server.stop();
    }

    void handleClient() override {
        _server.handleClient();
    }

    bool hasArg(const char* name) override {
        return _server.hasArg(name);
    }

    const char* arg(const char* name) override {
        _argBuffer = _server.arg(name);
        return _argBuffer.c_str();
    }

    const char* uri() override {
        _uriBuffer = _server.uri();
        return _uriBuffer.c_str();
    }

    void send(int code, const char* content_type, const char* content) override {
        _server.send(code, content_type, content);
    }

    // Expose the underlying server for special operations
    WebServer& getServer() { return _server; }

private:
    WebServer _server;
    String _argBuffer;
    String _uriBuffer;
};

#endif // WEB_SERVER_ADAPTER_H
