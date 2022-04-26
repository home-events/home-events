from adafruit_wiznet5k.adafruit_wiznet5k import *
import time


class Sniffer:
    def __init__(self, interface, debug=False):
        self._the_interface = interface
        self._debug = debug
        self._socknum = self._the_interface.get_socket()
        if self._debug:
            print("Socket number is: ", self._socknum)
        assert self._socknum == 0, "MACRAW socket must be socket 0"

    def __exit__(self):
        self._close_socket()

    def _read_s0cr(self):
        while True:
            s0_cr = self._the_interface._read_sncr(self._socknum)
            if self._debug:
                print("Socket 0 CR: ", s0_cr)
            if s0_cr[0] == 0x00:
                break
            time.sleep(0.00025)

    def _open_socket(self):
        self._the_interface._write_snmr(self._socknum, SNMR_MACRAW)
        self._the_interface._write_snir(self._socknum, 0xFF)  # todo: do we need interrupts handled at this point? what 0xFF does for interrupts?
        self._the_interface._write_sncr(self._socknum, CMD_SOCK_OPEN)
        self._read_s0cr()
        assert self._the_interface._read_snsr(self._socknum)[0] == SNSR_SOCK_MACRAW, "Socket must be in MACRAW mode"

    def _close_socket(self):
        self._the_interface.socket_close(self._socknum)

    def _listen(self):
        self._the_interface._write_sncr(self._socknum, CMD_SOCK_LISTEN)
        self._read_s0cr()

    def start(self):
        self._open_socket()
        self._listen()

    def stop(self):
        self._close_socket()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()

    def next_packet(self):
        return self._the_interface.socket_read(self._socknum, 65565)
