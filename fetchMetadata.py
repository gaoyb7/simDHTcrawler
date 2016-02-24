import socket

from btdht import gen_node_id
from struct import pack, unpack

PROTOCOL_ID = b"BitTorrent protocol"

def send_handshake(s, infohash):
    nid = gen_node_id()
    header = chr(len(PROTOCOL_ID)).encode() + PROTOCOL_ID
    reserved = b"\x00\x00\x00\x00\x00\x10\x00\x00"
    msg = header + reserved + infohash + nid
    s.send(msg)


def send_extension_handshake(s, infohash):
    pass
