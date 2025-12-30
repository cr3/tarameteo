#ifndef X509_PARSER_H
#define X509_PARSER_H

#include <stddef.h>
#include <stdint.h>

/**
 * @brief Lightweight X.509 certificate parser for ESP32
 *
 * This class wraps mbedTLS X.509 functions to provide certificate parsing
 * capabilities while keeping the interface testable.
 */
class X509Parser {
public:
    static const int MAX_CN_LENGTH = 64;
    static const int MAX_SERIAL_LENGTH = 64;

    /**
     * @brief Extract the Common Name (CN) from a PEM certificate
     *
     * @param certPem PEM-encoded certificate string
     * @param cnBuffer Buffer to store the extracted CN
     * @param bufferSize Size of the CN buffer
     * @return true if CN was successfully extracted, false otherwise
     */
    static bool extractCN(const char* certPem, char* cnBuffer, size_t bufferSize);

    /**
     * @brief Extract the expiration timestamp from a PEM certificate
     *
     * @param certPem PEM-encoded certificate string
     * @param expiresAt Pointer to store the expiration timestamp (Unix epoch seconds)
     * @return true if expiration was successfully extracted, false otherwise
     */
    static bool extractExpiration(const char* certPem, unsigned long* expiresAt);

    /**
     * @brief Extract the certificate serial number
     *
     * @param certPem PEM-encoded certificate string
     * @param serialBuffer Buffer to store the serial number (hex string)
     * @param bufferSize Size of the serial buffer
     * @return true if serial was successfully extracted, false otherwise
     */
    static bool extractSerial(const char* certPem, char* serialBuffer, size_t bufferSize);

    /**
     * @brief Verify that a private key matches a certificate's public key
     *
     * This performs cryptographic verification that the private key and
     * certificate form a valid pair.
     *
     * @param certPem PEM-encoded certificate string
     * @param keyPem PEM-encoded private key string
     * @return true if the key pair is valid, false otherwise
     */
    static bool validateKeyPair(const char* certPem, const char* keyPem);

    /**
     * @brief Get detailed certificate information for debugging
     *
     * @param certPem PEM-encoded certificate string
     * @param infoBuffer Buffer to store certificate info
     * @param bufferSize Size of the info buffer
     * @return true if info was retrieved, false otherwise
     */
    static bool getCertificateInfo(const char* certPem, char* infoBuffer, size_t bufferSize);

private:
    /**
     * @brief Convert mbedTLS time structure to Unix epoch seconds
     */
    static unsigned long timeToEpoch(int year, int month, int day, int hour, int min, int sec);
};

#endif // X509_PARSER_H
