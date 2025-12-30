#!/bin/sh

# Configuration
LE_DIR=/etc/letsencrypt

# Copy primary private key and full chain to live directory
cp ${LE_DIR}/live/${SERVER_HOSTNAME}/privkey.pem ${LE_DIR}/live/privkey.pem
cp ${LE_DIR}/live/${SERVER_HOSTNAME}/fullchain.pem ${LE_DIR}/live/fullchain.pem
