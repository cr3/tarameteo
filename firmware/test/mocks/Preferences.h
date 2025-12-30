#ifndef PREFERENCES_H
#define PREFERENCES_H

#ifdef UNIT_TEST

#include <string>
#include <cstring>
#include <map>

// Mock Preferences class for unit testing
class Preferences {
public:
    bool begin(const char* name, bool readOnly = false) {
        _namespace = name;
        _readOnly = readOnly;
        return true;
    }

    void end() {
        // Nothing to do
    }

    size_t putString(const char* key, const char* value) {
        if (_readOnly) return 0;
        _storage[std::string(key)] = std::string(value);
        return strlen(value);
    }

    size_t getString(const char* key, char* buffer, size_t maxLen) {
        auto it = _storage.find(std::string(key));
        if (it == _storage.end()) {
            buffer[0] = '\0';
            return 0;
        }
        strncpy(buffer, it->second.c_str(), maxLen - 1);
        buffer[maxLen - 1] = '\0';
        return it->second.length();
    }

    size_t putULong(const char* key, unsigned long value) {
        if (_readOnly) return 0;
        _ulongs[std::string(key)] = value;
        return sizeof(unsigned long);
    }

    unsigned long getULong(const char* key, unsigned long defaultValue) {
        auto it = _ulongs.find(std::string(key));
        if (it == _ulongs.end()) return defaultValue;
        return it->second;
    }

    size_t putInt(const char* key, int value) {
        if (_readOnly) return 0;
        _ints[std::string(key)] = value;
        return sizeof(int);
    }

    int getInt(const char* key, int defaultValue) {
        auto it = _ints.find(std::string(key));
        if (it == _ints.end()) return defaultValue;
        return it->second;
    }

    bool isKey(const char* key) {
        return _storage.find(std::string(key)) != _storage.end();
    }

    bool clear() {
        _storage.clear();
        _ulongs.clear();
        _ints.clear();
        return true;
    }

    // Helper for tests to inject data
    void _mockSetString(const char* key, const char* value) {
        _storage[std::string(key)] = std::string(value);
    }

private:
    std::string _namespace;
    bool _readOnly = false;
    std::map<std::string, std::string> _storage;
    std::map<std::string, unsigned long> _ulongs;
    std::map<std::string, int> _ints;
};

#endif // UNIT_TEST
#endif // PREFERENCES_H
