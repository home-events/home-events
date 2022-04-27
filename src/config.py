# coding: utf-8
import json


class Config:
    def __init__(self, file='config.json'):
        self.__config_file = file
        self.__config = {}

    def load(self):
        with open(self.__config_file, 'r') as f:
            self.__config = json.load(f)

    def save(self):
        with open(self.__config_file, 'w') as f:
            json.dump(self.__config, f)

    def mac_address_to_devices(self):
        devices_map = {d['mac']: d['name'] for d in self.__config['devices']}
        return devices_map

    def tracking_devices(self, field='name'):
        return [d[field] for d in self.__config['devices'] if 'track' in d and d['track']]

    def mqtt_config(self):
        return self.__config['mqtt']

    def stats_config(self):
        return self.__config.get("stats", {"enabled": False, "interval": 60})

    def network_config(self):
        return self.__config.get("network",
                                 {"ip": "192.168.0.211", "mask": "255.255.255.0", "gateway": "192.168.0.1", "dns": "8.8.8.8", "mac": "c2:f1:cb:05:48:b6"})

    def notify_enabled(self):
        return self.__config.get("notify", {"enabled": False})['enabled']

    def web_server_enabled(self):
        return self.__config.get("web", {"enabled": False})['enabled']