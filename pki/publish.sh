#!/bin/sh

set -eu

PKI_DIR="${PKI_DIR:-/pki}"
TRUST_DIR="${TRUST_DIR:-/trust}"

mkdir -p "$TRUST_DIR"

echo "PKI: Publishing CA cert to trust volume"
cp -f "$PKI_DIR/ca.crt" "$TRUST_DIR/ca.crt"
chmod 644 "$TRUST_DIR/ca.crt" || true
