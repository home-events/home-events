.PHONY: test

TARGET_VOL ?= /Volumes/CIRCUITPY/
SERIAL_PORT ?= /dev/cu.usbmodem14101

MQTT_SERVER ?= $(shell cat src/config.json | jq -r .mqtt.host)
MQTT_USER ?= $(shell cat src/config.json | jq -r .mqtt.username)
MQTT_PASSWORD ?= $(shell cat src/config.json | jq -r .mqtt.password)
MQTT_TOPIC ?= $(shell cat src/config.json | jq -r .mqtt.topic)

cp-to-pico:
	cp -r src/* $(TARGET_VOL)
	ls -lash $(TARGET_VOL)

screen:
	screen $(SERIAL_PORT)

sub-mqtt-topics:
	@echo "subscribing to mqtt topic: $(MQTT_TOPIC)/#"
	@mosquitto_sub -v -q 1 -h $(MQTT_SERVER) -u $(MQTT_USER) -P $(MQTT_PASSWORD)  -t "$(MQTT_TOPIC)/#"
