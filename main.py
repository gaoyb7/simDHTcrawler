import bencodepy
import codecs
import socket
import threading

from btdht import btdht
from fetchMetadata import fetch_metadata
from queue import Queue
from time import sleep
from sqlalchemy import create_engine, Table, String, MetaData, Column
from sqlalchemy.sql import select

metadata = MetaData()

hash_tab = Table("hash_tab", metadata,
        Column("infohash", String(40), primary_key=True),
        Column("name", String(128)),
        )

class Master(threading.Thread):
    def __init__(self):
        super().__init__()
        self.setDaemon(True)
        self.que = Queue()
        self.conn = create_engine("postgresql://gaoyb7@localhost/dht_demo").connect()
        self.ins = hash_tab.insert()

    def log_in_database_demo(self, infohash, name):
        try:
            self.conn.execute(self.ins, infohash=infohash, name=name)
        except Exception as e:
            pass

    def logger(self):
        while True:
            if self.que.empty():
                sleep(1)
                continue
            else:
                r = self.que.get()
                self.log_in_database_demo(r[1], r[2])

    def run(self):
        #while True:
        #    self.fetch()
        dt = threading.Thread(target=self.logger)
        dt.setDaemon(True)
        dt.start()
        while True:
            if threading.activeCount() < 1500:
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
        #print("%s %s" % (codecs.encode(infohash, "hex_codec").decode(), name.decode("utf-8")))
        #fetch_metadata(nid, infohash, address)
        #print(self.que.qsize())
        if self.que.qsize() > 5000:
            sleep(1)
        self.que.put([nid, codecs.encode(infohash, "hex_codec").decode(), name.decode()])
        #print(self.que.qsize())
        #print(infohash, self.que.qsize(), threading.activeCount())


if __name__ == "__main__":
    master = Master()
    master.start()
    dht = btdht(master, "0.0.0.0", 6881, 100)
    dht.start()
    dht.auto_send_find_node()
