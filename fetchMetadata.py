"""
Reference:
Bittorrent Protocol: https://zh.wikibooks.org/zh/BitTorrent%E5%8D%8F%E8%AE%AE%E8%A7%84%E8%8C%83
BEPs 09: http://bittorrent.org/beps/bep_0009.html
BEPs 10: http://bittorrent.org/beps/bep_0010.html
"""
import socket
import bencodepy

from btdht import gen_node_id
from struct import pack, unpack


BT_PROTOCOL = b"BitTorrent protocol"
BT_EXT_MSG_ID = b"\x14"
BT_EXT_HANDSHAKE_ID = b"\x00"

def send_msg(s, msg):
    msg_len = pack(">I", len(msg))
    s.send(msg_len + msg)


def send_handshake(s, nid, infohash):
    pstr = BT_PROTOCOL
    pstrlen = chr(len(BT_PROTOCOL)).encode()
    reserved = b"\x00\x00\x00\x00\x00\x10\x00\x00"
    msg = pstrlen + pstr + reserved + infohash + nid
    s.send(msg)


def send_ext_handshake(s):
    msg_body = {"m": {"ut_metadata": 3}}
    msg = BT_EXT_MSG_ID + BT_EXT_HANDSHAKE_ID + bencodepy.encode(msg_body)
    send_msg(s, msg)


def chk_handshake_response(msg, infohash):
    try:
        pstrlen, msg = ord(msg[:1]), msg[1:]
        if pstrlen != len(BT_PROTOCOL):
            return False
    except Exception:
        return False

    try:
        pstr, msg = msg[:pstrlen], msg[pstrlen:]
        info_hash = msg[8:28]
    except Exception:
        return False
    if pstr != BT_PROTOCOL or info_hash != infohash:
        return False

    return True


def fetch_metadata(nid, infohash, address):
    try:
        print("in fetch_metadata")
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(5)
        s.connect(address)

        send_handshake(s, nid, infohash)
        msg = s.recv(4096)

        if not chk_handshake_response(msg, infohash):
            print("error in chk handshake")
            return

        send_ext_handshake(s)
        msg = s.recv(4096)

        print(msg)
    except socket.timeout:
        print("timeout")
    except Exception:
        pass
    finally:
        s.close()
