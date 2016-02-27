import bencodepy
import codecs
import socket
import threading

from btdht import btdht
from fetchMetadata import fetch_metadata
from queue import Queue
from time import sleep

class Master(threading.Thread):
    def __init__(self):
        super().__init__()
        self.setDaemon(True)
        self.que = Queue()

    def run(self):
        #while True:
        #    self.fetch()
        while True:
            if threading.activeCount() < 200:
                if self.que.qsize() == 0:
                    sleep(1)
                    continue
                r = self.que.get()
                t = threading.Thread(target=fetch_metadata, args=(r[0], r[1], r[2]))
                t.setDaemon(True)
                t.start()
            else:
                sleep(1)


    def fetch(self):
        for i in range(100):
            if self.que.qsize() == 0:
                sleep(1)
                continue
            r = self.que.get()
            t = threading.Thread(target=fetch_metadata, args=(r[0], r[1], r[2]))
            t.setDaemon(True)
            t.start()

    def log(self, nid, infohash, name, address):
        print("%s %s" % (codecs.encode(infohash, "hex_codec").decode(), name.decode()))
        #fetch_metadata(nid, infohash, address)
        #self.que.put([nid, infohash, address])
        #print(self.que.qsize())
        #print(infohash, self.que.qsize(), threading.activeCount())


if __name__ == "__main__":
    master = Master()
    master.start()
    dht = btdht(master, "0.0.0.0", 6881, 200)
    dht.start()
    dht.auto_send_find_node()
