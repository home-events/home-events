import board
import busio
import digitalio
from adafruit_wiznet5k.adafruit_wiznet5k import WIZNET5K

from config import Config
from mapper import Mapper
from notifier import MqttNotifier
from packet_decoder import decode_packet
from inference import *
from sniffer import Sniffer
from stats import PacketStats
from web_server import web_server_instance
import gc

##SPI0
SPI0_SCK = board.GP18
SPI0_TX = board.GP19
SPI0_RX = board.GP16
SPI0_CSn = board.GP17

W5x00_RSTn = board.GP20

print("Home-Events v0.1")
config = Config()
config.load()

net_config = config.network_config()

MY_MAC = tuple(int(e, 16) for e in net_config["mac"].split(':'))
IP_ADDRESS = tuple(map(int, net_config["ip"].split('.')))
SUBNET_MASK = tuple(map(int, net_config["mask"].split('.')))
GATEWAY_ADDRESS = tuple(map(int, net_config["gateway"].split('.')))
DNS_SERVER = tuple(map(int, net_config["dns"].split('.')))

ethernetRst = digitalio.DigitalInOut(W5x00_RSTn)
ethernetRst.direction = digitalio.Direction.OUTPUT

cs = digitalio.DigitalInOut(SPI0_CSn)
cs.direction = digitalio.Direction.OUTPUT

ethernetRst.value = False
cs.value = True
time.sleep(0.1)
ethernetRst.value = True

spi_bus = busio.SPI(SPI0_SCK, MOSI=SPI0_TX, MISO=SPI0_RX)
time.sleep(0.1)

eth = WIZNET5K(spi_bus, cs, is_dhcp=False, mac=MY_MAC, debug=False)
eth.ifconfig = (IP_ADDRESS, SUBNET_MASK, GATEWAY_ADDRESS, DNS_SERVER)

print("Chip Version:", eth.chip)
print("MAC:", [hex(i) for i in eth.mac_address])
print("IP:", eth.pretty_ip(eth.ip_address))

mapper = Mapper(config.mac_address_to_devices())
sniffer = Sniffer(eth, debug=False)

mqtt_config = config.mqtt_config()
notifier = MqttNotifier(eth=eth, host=mqtt_config['host'], topic=mqtt_config['topic'], mqtt_user=mqtt_config['username'], mqtt_password=mqtt_config['password'])

stats_notify_callback = None
stats_config = config.stats_config()
if stats_config['notify']:
    stats_notify_callback = notifier.notify
    print(f"Stats will be sent to MQTT, config: {stats_config}")

stats = PacketStats(mapper, notify_callback=stats_notify_callback, notify_every_seconds=stats_config['interval'])

inference_engine = SimpleRuleEngine(devices_to_track=config.tracking_devices(), notify_callback=notifier.notify, track_callback=stats.track)

sniffer.start()
web_server_instance.begin(eth, stats)
notifier.start()

packet_idx = 0
while True:
    web_server_instance.loop()
    size, buf = sniffer.next_packet()
    if size < 0:
        continue
    print("Packet:", packet_idx)
    packet = decode_packet(buf[2:])  # first 2 bytes are the size of the buffer
    mapper.map_packet(packet, map_unknown_to='')
    stats.update(packet)
    inference_engine.update(packet)
    packet_idx += 1
    gc.collect()
