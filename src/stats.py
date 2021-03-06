# coding: utf-8
from collections import OrderedDict


class PacketStats:
    def __init__(self, mapper, notify_every_seconds=60, max_packet_size=20):
        self.packets_count = 0
        self.packet_types = OrderedDict()
        self.mapper = mapper
        self.stats = OrderedDict()
        self.tracking = OrderedDict()
        self.notify_every_seconds = notify_every_seconds
        self.max_packet_size = max_packet_size

    def track(self, device, event):
        self.tracking[device] = event

    def update(self, packet):
        self.packets_count += 1
        packet_type = packet['type']
        if packet_type not in self.packet_types:
            self.packet_types[packet_type] = 1
        else:
            self.packet_types[packet_type] += 1
        src_mac = packet['src_mac']
        src_device = packet['src_device']
        dst_mac = packet['dst_mac']
        dst_device = packet['dst_device']

        if len(self.stats) > self.max_packet_size:
            self.stats.popitem()

        key = (src_mac, dst_mac)
        if key not in self.stats:
            self.stats[key] = {
                'src_mac': src_mac,
                'src_device': src_device,
                'dst_mac': dst_mac,
                'dst_device': dst_device,
                'packets_count': 1,
                'packet_types': {packet_type: 1},
                'src_ip': '',
                'dst_ip': '',
            }
        else:
            self.stats[key]['packets_count'] += 1
            if packet_type == 'unknown':
                packet_type = f"{packet['eth_proto']:x}"

            if packet_type not in self.stats[key]['packet_types']:
                self.stats[key]['packet_types'][packet_type] = 1
            else:
                self.stats[key]['packet_types'][packet_type] += 1

        if packet_type == 'ipv4' and 'error' not in packet['ip_packet']:
            self.stats[key]['src_ip'] = packet['ip_packet']['src_ip']
            self.stats[key]['dst_ip'] = packet['ip_packet']['dst_ip']
