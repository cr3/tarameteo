ARG MOSQUITTO_VERSION=2.0
FROM eclipse-mosquitto:${MOSQUITTO_VERSION}

RUN apk add --no-cache envsubst

COPY docker-entrypoint.sh /
ENTRYPOINT ["/docker-entrypoint.sh"]

EXPOSE 8883

CMD ["/usr/sbin/mosquitto", "-c", "/mosquitto/config/mosquitto.conf"]
