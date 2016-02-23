import bencodepy
import codecs
import socket

from btdht import btdht
from fetchMetadata import send_handshake

class Master(object):
    def log(self, infohash, name, address):
        print("%s %s" % (codecs.encode(infohash, "hex_codec").decode(), name.decode()))
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(5)
        s.connect(address)

        send_handshake(s, infohash)
        packet = s.recv(4096)
        print(packet)


if __name__ == "__main__":
    dht = btdht(Master(), "0.0.0.0", 6881, 200)
    dht.start()
    dht.auto_send_find_node()
