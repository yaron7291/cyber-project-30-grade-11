__author__ = 'yaron'

# from  tcp_by_size import send_with_size ,recv_by_size
import hmac
import hashlib
from inspect import signature

SIZE_HEADER_FORMAT = "0000000|" # n digits for data size + one delimiter
size_header_size = len(SIZE_HEADER_FORMAT)
TCP_DEBUG = True
LEN_TO_PRINT = 100
SECRET_KEY = b'my_secret_tank_key'

def recv_by_size(sock):
    size_header = b''
    data_len = 0
    while len(size_header) < size_header_size:
        _s = sock.recv(size_header_size - len(size_header))
        if _s  is None:
            size_header = b''
            break
        size_header += _s
    data_with_sig  = b''
    if size_header != b'':
        data_len = int(size_header[:size_header_size - 1])
        while len(data_with_sig) < data_len:
            _d = sock.recv(data_len - len(data_with_sig))
            if _d == b'':
                data  = b''
                break
            data_with_sig += _d
    if not data_with_sig:
        return b''
    try:
        data , recvsig = data_with_sig.split(b"|SIG|", 1)
        expdsig = hmac.new(SECRET_KEY, data, hashlib.sha512).digest()
        if hmac.compare_digest(recvsig, expdsig):
            if TCP_DEBUG:
                print(f"\nRecv verified >> {data[:LEN_TO_PRINT]}")
                return data
        else:
            print("\n[SECURITY ALERT] Signature mismatch! Message might be tampered.")
            return b''
    except Exception as e:
        print(f"\n[ERROR] {e}")
        return b''
    return b''


def send_with_size(sock, data):
    if type(data) == str:
        data = data.encode()
    signature = hmac.new(SECRET_KEY,data, hashlib.sha512).digest()
    payload = data + b"|SIG|" + signature
    len_payload = len(payload)
    header_data = str(len_payload).zfill(size_header_size - 1) + "|"
    bytea = header_data.encode() + payload

    sock.send(bytea)

    if TCP_DEBUG and len_payload > 0:
        print(f"\nSent({len_payload})>>>{bytea[:LEN_TO_PRINT]}")



