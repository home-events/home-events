import struct

ethernet_proto_map = {
    0x0800: 'IPv4',
    0x86DD: 'IPv6',
    0x0806: 'ARP',
    0x0842: 'WOL',
    0x8808: 'EAPOL',
}

ip4_proto_map = {
    1: 'ICMP',
    2: 'IGMP',
    6: 'TCP',
    17: 'UDP',
    47: 'GRE',
    50: 'ESP',
    51: 'AH',
    57: 'SKIP',
    88: 'EIGRP',
    89: 'OSPF',
    115: 'L2TP',
}


def _format_ip_addr(addr):
    return '.'.join(map(str, addr))


def _format_mac_addr(addr):
    return ':'.join(map('{:02x}'.format, addr))


def _unpack_ethernet_frame(data):
    try:
        dst_mac, src_mac, proto = struct.unpack('!6s6sH', data[:14])
        return _format_mac_addr(dst_mac), _format_mac_addr(src_mac), proto, data[14:]
    except Exception as e:
        print(e)
        return None, None, None, []


def _decode_ip_packet(data):
    try:
        version_header_length = data[0]
        version = version_header_length >> 4
        header_length = (version_header_length & 0x0F) << 2
        ttl, proto, src_ip, dst_ip = struct.unpack('!8xBB2x4s4s', data[:20])
        return _format_ip_addr(src_ip), _format_ip_addr(dst_ip), proto, ttl, header_length, version, data[header_length:]
    except Exception as e:
        print(e)
        return None, None, None, None, None, []


def _decode_ip_v6_packet(data):
    try:
        # unpack IPv6 header using struct
        # todo fixme, getting error 'buffer size must match format'
        version, traffic_class, flow_label, payload_length, next_header, hop_limit, src_ip, dst_ip = struct.unpack('!6xBBHHBB16s16s', data[:40])
        #
        # b = bytearray(data.read(4))
        #
        # version = (b[0] >> 4) & 0x0F
        # traffic_class = ((b[0] & 0x0F) << 4) | ((b[1] >> 4) & 0x0F)
        # flow_label = ((b[1] & 0x0F) << 16) | (b[2] << 8) | b[3]
        #
        #
        # payload_length = struct.unpack(">H", data.read(2))[0]
        # next_header = ord(data.read(1))
        # hop_limit = ord(data.read(1))
        # src_ip = bytearray(data.read(16))
        # dst_ip = bytearray(data.read(16))

        return _format_ip_addr(src_ip), _format_ip_addr(dst_ip), version, traffic_class, flow_label, hop_limit, next_header, payload_length, data[40:]
    except Exception as e:
        print(e)
        return None, None, None, None, None, None, None, None, []


def _decode_arp_packet(data):
    try:
        htype, ptype, hlen, plen, opcode = struct.unpack('!HHBBH', data[:8])
        return htype, ptype, hlen, plen, opcode, data[8:]
    except Exception as e:
        print(e)
        return None


def _decode_icmp_packet(data):
    try:
        icmp_type, code, checksum = struct.unpack('!BBH', data[:4])
        return icmp_type, code, checksum, data[4:]
    except Exception as e:
        print(e)
        return None


def decode_packet(data):
    dst_mac, src_mac, eth_proto, payload = _unpack_ethernet_frame(data)
    packet = {'dst_mac': dst_mac, 'src_mac': src_mac, 'eth_proto': eth_proto, 'type': 'unknown'}

    if eth_proto == 0x0800:  # IPv4
        try:
            src_ip, dst_ip, ip_proto, ttl, header_length, version, payload = _decode_ip_packet(payload)
            packet['ip_packet'] = {'src_ip': src_ip, 'dst_ip': dst_ip, 'ip_proto': ip_proto, 'ttl': ttl, 'header_length': header_length, 'version': version}
            packet['type'] = 'ipv4'
            if ip_proto == 1:  # ICMP
                icmp_type, code, checksum, payload = _decode_icmp_packet(payload)
                packet['ip_packet']['icmp_packet'] = {'type': icmp_type, 'code': code, 'checksum': checksum}
        except Exception as e:
            print(e)
            packet['ip_packet'] = {'error': 'IPv4 packet decode error'}
    elif eth_proto == 0x86DD:  # IPv6
        packet['type'] = 'ipv6'
        src_ip, dst_ip, version, traffic_class, flow_label, hop_limit, next_header, payload_length, payload = _decode_ip_v6_packet(payload)
        packet['ip_v6_packet'] = {'src_ip': src_ip, 'dst_ip': dst_ip, 'version': version, 'traffic_class': traffic_class, 'hop_limit': hop_limit,
                                  'payload_length': payload_length}
        if next_header == 0x3A:  # ICMPv6
            icmp_type, code, checksum, payload = _decode_icmp_packet(payload) # todo: check this
            packet['ip_v6_packet']['icmp_packet'] = {'type': icmp_type, 'code': code, 'checksum': checksum}
    elif eth_proto == 0x0806:  # ARP
        try:
            htype, ptype, hlen, plen, opcode, payload = _decode_arp_packet(payload)
            packet['type'] = 'arp'
            packet['arp_packet'] = {'htype': htype, 'ptype': ptype, 'hlen': hlen, 'plen': plen, 'opcode': opcode}
        except Exception as e:
            print(e)
            packet['arp_packet'] = {'error': 'ARP packet decode error'}
    elif eth_proto == 0x01:  # ICMP
        try:
            icmp_type, code, checksum, payload = _decode_icmp_packet(payload)
            packet['type'] = 'icmp'
            packet['icmp_packet'] = {'icmp_type': icmp_type, 'code': code, 'checksum': checksum}
        except Exception as e:
            print(e)
            packet['icmp_packet'] = {'error': 'ICMP packet decode error'}

    return packet
