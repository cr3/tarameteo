#!/bin/sh

: "${MQTT_USERNAME:?}"
: "${MQTT_PASSWORD:?}"
: "${MOSQUITTO_TEMPLATE:?}"

MOSQUITTO_CONFIG_DIR=${MOSQUITTO_CONFIG_DIR:-/mosquitto/config}
MOSQUITTO_DATA_DIR=${MOSQUITTO_DATA_DIR:-/mosquitto/data}

# Create conf from template.
MOSQUITTO_CONF=${MOSQUITTO_CONFIG_DIR}/mosquitto.conf
install -o mosquitto -g mosquitto -m 600 /dev/null ${MOSQUITTO_CONF}
export MOSQUITTO_CONFIG_DIR MOSQUITTO_DATA_DIR
envsubst < ${MOSQUITTO_TEMPLATE} > ${MOSQUITTO_CONF}

# Copy certs from letsencrypt.
LE_DIR=/etc/letsencrypt
MOSQUITTO_CERTS_DIR=${MOSQUITTO_CONFIG_DIR}/certs
install -d -o mosquitto -g mosquitto -m 700 ${MOSQUITTO_CERTS_DIR}
install -o mosquitto -g mosquitto -m 600 \
  ${LE_DIR}/live/privkey.pem \
  ${MOSQUITTO_CERTS_DIR}/key.pem
install -o mosquitto -g mosquitto -m 644 \
  ${LE_DIR}/live/fullchain.pem \
  ${MOSQUITTO_CERTS_DIR}/cert.pem

# Initialize dynsec config.
DYNSEC_CONFIG=${MOSQUITTO_DATA_DIR}/dynamic-security.json
if [ ! -e "${DYNSEC_CONFIG}" ]; then
  echo -e "${MQTT_PASSWORD}\n${MQTT_PASSWORD}" \
  | mosquitto_ctrl dynsec init ${DYNSEC_CONFIG} ${MQTT_USERNAME}
  chown mosquitto:mosquitto "${DYNSEC_CONFIG}"
fi

exec "$@"
