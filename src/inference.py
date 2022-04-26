# coding: utf-8
import json
import time


class SimpleRuleEngine:
    def __init__(self, devices_to_track,
                 notify_callback=None,
                 track_callback=None,
                 consecutive_packet_delay_sec=2,
                 max_no_packet_sec=300,
                 min_seen_count=3):
        self.devices_to_track = devices_to_track
        self.seen_devices = {}
        self.consecutive_packet_delay_sec = consecutive_packet_delay_sec
        self.min_seen_count = min_seen_count
        self.max_no_packet_sec = max_no_packet_sec
        self.notify_callback = notify_callback
        self.track_callback = track_callback

    def update(self, packet):
        device = None
        if packet['src_device'] in self.devices_to_track:
            device = packet['src_device']
        if packet['dst_device'] in self.devices_to_track:
            device = packet['dst_device']
        if not device:
            return

        seen_device = self.seen_devices.get(device, {'last_seen': 0, 'seen_count': 0, 'first_seen': 0, 'appeared_since': 0, 'disappeared_since': 0})
        prev_last_seen = seen_device['last_seen']
        now = time.time()
        seen_device['last_seen'] = now
        first_seen = seen_device['first_seen']
        if first_seen == 0:
            seen_device['first_seen'] = now

        since_last_seen = seen_device['last_seen'] - prev_last_seen

        # increase count if there are two consecutive packets from the device in the past 30s
        if since_last_seen >= self.consecutive_packet_delay_sec:
            seen_device['seen_count'] += 1
        seen_device['previous_seen'] = prev_last_seen
        print(f"{device}: {seen_device}")
        # if there is a wide gap between first seen and last seen
        # and at least 3 packets from device, then consider device as "appearing"
        if first_seen >= 0 and seen_device['appeared_since'] == 0 \
                and seen_device['last_seen'] - first_seen > self.consecutive_packet_delay_sec \
                and seen_device['seen_count'] >= self.min_seen_count:
            seen_device['appeared_since'] = now
            seen_device['disappeared_since'] = 0
            print(f"{device} appearing: {seen_device}")
            event = {'type': 'appeared', 'data': seen_device}
            if self.notify_callback is not None:
                self.notify_callback(device, message=json.dumps(event))
            if self.track_callback is not None:
                self.track_callback(device, event)

        self.seen_devices[device] = seen_device

        self._check_disappeared()

    def _check_disappeared(self):
        # check other tracked devices, if no packet received from a dvice for a while, mark it as disappeared
        for tracked_device in self.devices_to_track:
            if tracked_device not in self.seen_devices or self.seen_devices[tracked_device]['appeared_since'] <= 0:
                continue
            seen_device = self.seen_devices[tracked_device]
            now = time.time()
            since_last_seen = now - seen_device['last_seen']
            if since_last_seen > self.max_no_packet_sec and seen_device['disappeared_since'] == 0:
                seen_device['appeared_since'] = 0
                seen_device['disappeared_since'] = now
                print(f"{tracked_device} disappeared: {seen_device}")
                event = {'type': 'disappeared', 'data': seen_device}
                if self.notify_callback is not None:
                    self.notify_callback(tracked_device, message=json.dumps(event))
                if self.track_callback is not None:
                    self.track_callback(tracked_device, event)

                self.seen_devices[tracked_device] = seen_device
