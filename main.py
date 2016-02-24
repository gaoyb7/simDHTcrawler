import bencodepy
import codecs
import socket

from btdht import btdht
from fetchMetadata import fetch_metadata

class Master(object):
    def log(self, nid, infohash, name, address):
        print("%s %s" % (codecs.encode(infohash, "hex_codec").decode(), name.decode()))
        fetch_metadata(nid, infohash, address)


if __name__ == "__main__":
    dht = btdht(Master(), "0.0.0.0", 6881, 200)
    dht.start()
    dht.auto_send_find_node()
