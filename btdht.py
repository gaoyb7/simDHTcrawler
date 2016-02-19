import bencodepy
import socket

from hashlib import sha1
from random import getrandbits, randint
from struct import pack, unpack
from threading import Timer, Thread
from time import sleep
from collections import deque
from codecs import encode as codecs_encode

from knode import Knode


# The mainline DHT bootstrap nodes
BOOTSTRAP_NODES = (
    ("dht.transmissionbt.com", 6881),
    ("router.utorrent.com", 6881),
    ("router.bittorrent.com", 6881)
)

TID_LENGTH = 2
RE_JOIN_DHT_INTERVAL = 3
TOKEN_LENGTH = 2
PACKET_SIZE = 65536


def gen_id(length):
    return "".join(chr(randint(0, 255)) for _ in range(length))
    #return bytearray(getrandbits(8) for i in range(length))


def gen_node_id():
    return sha1(gen_id(20).encode()).digest()


def decode_krpc_nodes(nodes_field):
    nodes = []
    length = len(nodes_field)
    if length % 26 != 0:
        return nodes

    for i in range(0, length, 26):
        nid = nodes_field[i:i+20]
        ip = socket.inet_ntoa(nodes_field[i+20:i+24])
        port = unpack("!H", nodes_field[i+24:i+26])[0]
        nodes.append(Knode(nid, ip, port))

    return nodes


def get_neighbor(target, nid, prefix=10):
    return target[:prefix] + nid[prefix:]


class btdht(Thread):
    def __init__(self, master, bind_ip, bind_port, max_nodes_size):
        super().__init__()
        self.setDaemon(True)
        self.max_nodes_size = max_nodes_size
        self.nid = gen_node_id()
        self.nodes = deque(maxlen=self.max_nodes_size)

        self.master = master
        self.bind_ip = bind_ip
        self.bind_port = bind_port
        
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.socket.bind((self.bind_ip, self.bind_port))

        self.process_request_func = {
            b"get_peers": self.process_get_peers_request,
            b"announce_peer": self.process_announce_peer_request
        }

    def send_krpc(self, msg, address):
        try:
            self.socket.sendto(bencodepy.encode(msg), address)
        except Exception:
            pass

    def send_find_node(self, address, nid=None):
        nid = get_neighbor(nid, self.nid) if nid else self.nid
        tid = gen_id(TID_LENGTH)

        msg = {
            "t": tid,
            "y": "q",
            "q": "find_node",
            "a": {
                "id": nid,
                "target": gen_node_id()
            }
        }

        self.send_krpc(msg, address)

    def join_dht(self):
        for address in BOOTSTRAP_NODES:
            self.send_find_node(address)

    def re_join_dht(self):
        if len(self.nodes) == 0:
            self.join_dht()
        Timer(RE_JOIN_DHT_INTERVAL, self.re_join_dht).start()

    def run(self):
        self.re_join_dht()
        while True:
            try:
                (data, address) = self.socket.recvfrom(PACKET_SIZE)
                msg = bencodepy.decode(data)
                self.process_message(msg, address)
                print(len(self.nodes))
            except Exception:
                pass

    def process_message(self, msg, address):
        try:
            # response message
            if msg[b"y"] == b"r":
                if msg[b"r"].get(b"nodes"):
                    self.process_find_node_response(msg, address)
            elif msg[b"y"] == b"q":
                try:
                    self.process_request_func[msg[b"q"]](msg, address)
                except IndexError:
                    self.play_dead(msg, address)
        except Exception:
            print("Error in process message")

    def process_find_node_response(self, msg, address):
        print("in process find node response")
        nodes = decode_krpc_nodes(msg[b"r"][b"nodes"])
        print("ok")
        for node in nodes:
            if len(node.nid) != 20: continue
            if node.ip == self.bind_ip: continue
            if node.port < 1 or node.port > 65535: continue
            self.nodes.append(node)

    def process_get_peers_request(self, msg, address):
        try:
            infohash = msg[b"a"][b"info_hash"]
            tid = msg[b"t"]
            nid = msg[b"a"][b"id"]
            token = infohash[:TOKEN_LENGTH]
            msg = {
                "t": tid,
                "y": "r",
                "r": {
                    "id": get_neighbor(infohash, self.nid),
                    "nodes": "",
                    "token": token
                }
            }
            self.send_krpc(msg, address)
        except Exception:
            pass

    def process_announce_peer_request(self, msg, address):
        try:
            infohash = msg[b"a"][b"info_hash"]
            self.master.log(infohash)
        except Exception:
            pass
        finally:
            try:
                tid = msg[b"t"]
                nid = msg[b"a"][b"id"]
                msg = {
                    "t": tid,
                    "y": "r",
                    "r": {
                        "id": get_neighbor(nid, self.nid)
                    }
                }
                self.send_krpc(msg, address)
            except Exception:
                pass

    def play_dead(self, msg, address):
        try:
            tid = msg[b"t"]
            msg = {
                "t": tid,
                "y": "e",
                "e": [202, "Server Error"]
            }
            self.send_krpc(msg, address)
        except Exception:
            pass

    def auto_send_find_node(self):
        wait_time = 1.0 / self.max_nodes_size
        while True:
            try:
                node = self.nodes.popleft()
                self.send_find_node((node.ip, node.port), node.nid)
            except Exception:
                pass
            sleep(wait_time)
