# coding: utf-8

import adafruit_minimqtt.adafruit_minimqtt as MQTT
import adafruit_wiznet5k.adafruit_wiznet5k_socket as socket


class MqttNotifier(object):
    def __init__(self, eth, host: str, mqtt_user: str, mqtt_password: str, port: int = 1883, topic: str = "notifications", client_id: str = "home-net-events"):
        MQTT.set_socket(socket, eth)
        self.mqtt_client = MQTT.MQTT(broker=host, username=mqtt_user, password=mqtt_password, port=port, client_id=client_id)
        self.mqtt_client.on_connect = self._on_connect
        self.mqtt_client.on_publish = self._on_publish
        self.topic = topic

    def start(self):
        self.mqtt_client.connect()

    def stop(self):
        self.mqtt_client.disconnect()

    def notify(self, device, message):
        self.mqtt_client.publish(topic=f"{self.topic}/{device}", msg=message, retain=False, qos=1)

    def _on_connect(self, client, userdata, flags, rc):
        self.notify("_mqtt_notifier", '{"message": "connected to MQTT broker."}')

    def _on_publish(self, client, _user_data, topic, _pid):
        print(f"published to MQTT topic: {topic}, data: {_user_data}, pid: {_pid}, client: {client}")

