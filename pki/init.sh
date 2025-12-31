#!/bin/sh

set -eu

PKI_DIR="${PKI_DIR:-/pki}"
CA_SUBJECT="${CA_SUBJECT:-/C=CA/ST=QC/L=Taram/O=TaramMeteo/OU=PKI/CN=TaramMeteo Root CA}"
CA_DAYS="${CA_DAYS:-3650}"

mkdir -p "$PKI_DIR"

umask 077

CA_KEY="$PKI_DIR/ca.key"
CA_CRT="$PKI_DIR/ca.crt"
if [ ! -s "$CA_KEY" ] || [ ! -s "$CA_CRT" ]; then
  echo "PKI: generating CA into $PKI_DIR"

  openssl genrsa -out "$CA_KEY" 4096

  openssl req -x509 -new -nodes \
    -key "$CA_KEY" \
    -sha256 -days "$CA_DAYS" \
    -out "$CA_CRT" \
    -subj "$CA_SUBJECT"
  chmod 600 "$CA_KEY" || true
  chmod 644 "$CA_CRT" || true
else
  echo "PKI: existing CA found in $PKI_DIR"
fi
