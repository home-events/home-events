# coding: utf-8

class Mapper:
    def __init__(self, mac_address_to_name_map, filter_unknown_mac_addresses=True):
        self.mac_address_to_name_map = mac_address_to_name_map
        self.filter_unknown_mac_addresses = filter_unknown_mac_addresses

    def map_to_name(self, mac_address, map_unknown_to=None):
        if mac_address in self.mac_address_to_name_map:
            return self.mac_address_to_name_map[mac_address]
        elif not self.filter_unknown_mac_addresses:
            return mac_address
        else:
            return map_unknown_to

    def map_packet(self, packet, map_unknown_to=None):
        packet['src_device'] = self.map_to_name(packet['src_mac'], map_unknown_to)
        packet['dst_device'] = self.map_to_name(packet['dst_mac'], map_unknown_to)
