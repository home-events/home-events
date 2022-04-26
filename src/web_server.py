import adafruit_requests as requests
import adafruit_wiznet5k.adafruit_wiznet5k_socket as socket
import adafruit_wiznet5k.adafruit_wiznet5k_wsgiserver as server
from adafruit_wiznet5k.adafruit_wiznet5k import *
from adafruit_wsgi.wsgi_app import WSGIApp

import microcontroller
import supervisor

import gc

# Here we create our application, registering the
# following functions to be called on specific HTTP GET requests routes
web_app = WSGIApp()


class MyWSGIServer(server.WSGIServer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def finish_response(self, result, client):
        try:
            response = "HTTP/1.1 {0}\r\n".format(self._response_status)
            for header in self._response_headers:
                response += "{0}: {1}\r\n".format(*header)
            response += "\r\n"
            client.send(response.encode("utf-8"))
            for data in result:
                if not isinstance(data, bytes):
                    data = data.encode("utf-8")
                if len(data) < 0x800:
                    client.send(data)
                else:
                    # split to chunks of 2 kb
                    data_chunks = [data[i:i + 0x800] for i in range(0, len(data), 0x800)]
                    for data_chunk in data_chunks:
                        client.send(data_chunk)

            gc.collect()
        finally:
            client.disconnect()
            client.close()


class WebServer:
    def __init__(self, *args, **kwargs):
        self.eth = None
        self.packet_stats = None
        self.wsgi_server = None

    def begin(self, eth, packet_stats):
        self.eth = eth
        self.packet_stats = packet_stats

        requests.set_socket(socket, eth)
        server.set_interface(eth)
        self.wsgi_server = MyWSGIServer(80, application=web_app)

        self.wsgi_server.start()

    def get_main_page(self):
        with open("web-ui/index.html", "r") as f:
            index_page_source = f.read()
        html = index_page_source.replace("$CHIPNAME", self.eth.chip)
        html = self._update_events_table(html)
        html = self._update_packets_table(html)
        return html

    def _update_events_table(self, html_string):
        events = self.packet_stats.tracking
        if len(events) < 1:
            return html_string.replace("$EVENTS_TABLE", "No events detected yet")

        events_view = """
                <table class="pure-table pure-table-striped">
                    <thead>
                        <tr>
                            <th>#</th>
                            <th>Device</th>
                            <th>Event</th>
                            <th>Since</th>
                        </tr>
                    </thead>
                    <tbody>"""
        print(events)
        i = 0
        for device, event in events.items():
            i += 1
            events_view += f"<tr><td>{i}</td><td>{device}</td><td>{event['type']}</td><td>{event}</td></tr>"
        events_view += "</tbody></table>"

        return html_string.replace("$EVENTS_TABLE", events_view)

    # todo: serve this as json (streaming) to avoid memory limit error
    def _update_packets_table(self, html_string):
        html_string = html_string.replace("$PACKETS_COUNT", str(self.packet_stats.packets_count))
        sorted_by_packet_count = sorted(self.packet_stats.stats.items(), key=lambda x: x[1]["packets_count"], reverse=True)
        packets_stats_view = """
                <table class="pure-table pure-table-striped">
                    <thead>
                        <tr>
                            <th>#</th>
                            <th>Source</th>
                            <th>Destination</th>
                            <th>Packets</th>
                            <th>Types</th>
                            <th>Source IP</th>
                            <th>Destination IP</th>
                        </tr>
                    </thead>
                    <tbody>"""

        i = 0
        for key, stat in sorted_by_packet_count:
            if i >= 20:
                break

            source = stat["src_device"]
            if len(source) < 1:
                source = stat["src_mac"]
            destination = stat["dst_device"]
            if len(destination) < 1:
                destination = stat["dst_mac"]
            packets = stat["packets_count"]
            source_ip = stat["src_ip"]
            destination_ip = stat["dst_ip"]

            packet_types = ", ".join(f"{t}: {c}" for t, c in stat["packet_types"].items())
            i += 1
            packets_stats_view += f"<tr><td>{i}</td><td>{source}</td><td>{destination}</td><td>{packets}</td><td>{packet_types}</td>\
                <td>{source_ip}</td><td>{destination_ip}</td></tr>"

        packets_stats_view += "</tbody></table>"
        return html_string.replace("$SNIFFED_PACKETS_STATS", packets_stats_view)

    def loop(self):
        self.wsgi_server.update_poll()
        self.eth.maintain_dhcp_lease()


web_server_instance = WebServer()


@web_app.route("/")
def root(request):  # pylint: disable=unused-argument
    return "200 OK", [("Connection", "close"), ("Content-Type", "text/html")], [web_server_instance.get_main_page()]


def static_file(path, content_type="text/html"):
    with open(path, "r") as f:
        data = f.read()
        response = ("200 OK", [("Connection", "close"), ("Content-Type", f"{content_type}; charset=utf-8"), ("Cache-Control", "max-age=604800")], [data])
        return response


@web_app.route("/home")
def home(request):  # pylint: disable=unused-argument
    return static_file("web-ui/index.html")


@web_app.route("/reload")
def reload(request):  # pylint: disable=unused-argument
    supervisor.reload()
    return home(request)


@web_app.route("/reset")
def reset(request):  # pylint: disable=unused-argument
    microcontroller.reset()
    return home(request)


@web_app.route("/css/pure-min.css")
def static_resources(request):  # pylint: disable=unused-argument
    return static_file("web-ui/pure-min.css", content_type="text/css")


@web_app.route("/css/styles.css")
def static_resources(request):  # pylint: disable=unused-argument
    return static_file("web-ui/styles.css", content_type="text/css")


@web_app.route("/css/grids-responsive-min.css")
def static_resources(request):  # pylint: disable=unused-argument
    return static_file("web-ui/grids-responsive-min.css", content_type="text/css")


@web_app.route("/img/github-mark.svg")
def static_resources(request):  # pylint: disable=unused-argument
    return static_file("web-ui/img/github-mark.svg", content_type="image/svg+xml")


@web_app.route("/img/network.svg")
def static_resources(request):  # pylint: disable=unused-argument
    return static_file("web-ui/img/network.svg", content_type="image/svg+xml")
