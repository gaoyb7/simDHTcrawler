"""
Fetch metadata from DHT network

Reference:
BEP-09: http://bittorrent.org/beps/bep_0009.html
BEP-10: http://bittorrent.org/beps/bep_0010.html
"""
import socket
import bencodepy

from btdht import gen_node_id
from struct import pack, unpack
from math import ceil
from time import time


BT_PROTOCOL = b"BitTorrent protocol"


def send_msg(s, msg):
    msg_len = pack(">I", len(msg))
    s.send(msg_len + msg)


def handshake(s, nid, infohash):
    """
    Send handshake message
    Format: <pstrlen><pstr><reserved><info_hash><peer_id>
    """
    pstr = BT_PROTOCOL
    pstrlen = chr(len(BT_PROTOCOL)).encode()
    reserved = b"\x00\x00\x00\x00\x00\x10\x00\x00"
    msg = pstrlen + pstr + reserved + infohash + nid
    s.send(msg)


def ext_handshake(s):
    """
    Format: <length prefix><message ID><payload>
    """
    msg_body = {"m": {"ut_metadata": 1}}
    msg = b"\x14\x00" + bencodepy.encode(msg_body)
    send_msg(s, msg)


def check_handshake_response(msg, infohash):
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


def decode_ext_handshake_msg(msg):
    str_ut_metadata = b"ut_metadata"
    ut_metadata = chr(msg[msg.index(str_ut_metadata) + len(str_ut_metadata) + 1])
    ut_metadata = int(ut_metadata)

    str_metadata_size = b"metadata_size"
    start = msg.index(str_metadata_size) + len(str_metadata_size) + 1
    msg = msg[start:]
    metadata_size = int(msg[:msg.index(b"e")])

    return ut_metadata, metadata_size


def send_request_metadata(s, ut_metadata, i):
    msg_body = {"m": {"msg_type": 0, "piece": i}}
    msg = b"\x14" + chr(ut_metadata).encode() + bencodepy.encode(msg_body)
    send_msg(s, msg)


def recv_piece(s, timeout=5):
    s.setblocking(0)
    data_list = []
    time_begin = time()
    
    while True:
        sleep(0.05)
        if data_list and time()-begin > timeout:
            break
        elif time()-begin() > timeout * 2:
            break
        try:
            data = s.recv(1024)
            if data:
                data_list.append(data)
                time_begin = time()
        except Exception:
            pass
    pkg = b"".join(data_list)
    pkg = pkg[pkg.index(b"ee")+2:]
    return pkg


def fetch_metadata(nid, infohash, address, timeout=5):
    try:
        print("in fetch_metadata")
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        s.connect(address)

        # handshake
        handshake(s, nid, infohash)
        msg = s.recv(4096)

        # verification
        if not check_handshake_response(msg, infohash):
            print("error in check handshake")
            return

        # advertize to support ut_metadata(BEP-09)
        ext_handshake(s)
        msg = s.recv(4096)

        ut_metadata, metadata_size = decode_ext_handshake_msg(msg)
        print("ut_metadata", ut_metadata, "metadata_size", metadata_size)

        metadata = []
        piece_tot = int(ceil(metadata_size / (1024 * 16)))
        for i in range(piece_tot):
            send_request_metadata(s, ut_metadata, i)
            piece = recv_piece(s, timeout)
            metadata.append(piece)

        metadata = b"".join(metadata)
        print(metadata)

    except socket.timeout:
        print("timeout")
    except Exception:
        pass
    finally:
        s.close()
