#ifndef PRINT_H_MOCK
#define PRINT_H_MOCK

#ifdef UNIT_TEST

// Print and Printable are already defined in Arduino.h
// This header just redirects to Arduino.h for compatibility
#include "Arduino.h"

#endif // UNIT_TEST
#endif // PRINT_H_MOCK
