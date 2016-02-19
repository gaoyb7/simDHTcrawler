import bencodepy
import codecs

from btdht import btdht

class Master(object):
    def log(self, infohash, name, address):
        print("%s %s" % (codecs.encode(infohash, "hex_codec").decode(), name.decode()))


if __name__ == "__main__":
    dht = btdht(Master(), "0.0.0.0", 6882, 200)
    dht.start()
    dht.auto_send_find_node()
