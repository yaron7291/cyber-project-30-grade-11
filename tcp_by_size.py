__author__ = 'yaron'

# from  tcp_by_size import send_with_size ,recv_by_size


SIZE_HEADER_FORMAT = "0000000|" # n digits for data size + one delimiter
size_header_size = len(SIZE_HEADER_FORMAT)
TCP_DEBUG = True
LEN_TO_PRINT = 100


def recv_by_size(sock):
    size_header = b''
    data_len = 0
    while len(size_header) < size_header_size:
        _s = sock.recv(size_header_size - len(size_header))
        if _s  is None:
            size_header = b''
            break
        size_header += _s
    data  = b''
    if size_header != b'':
        data_len = int(size_header[:size_header_size - 1])
        while len(data) < data_len:
            _d = sock.recv(data_len - len(data))
            if _d == b'':
                data  = b''
                break
            data += _d

    if TCP_DEBUG and size_header is not None:
        print(f"\nRecv({int(size_header[:-1])})>>>{data[:LEN_TO_PRINT]}")
    if data_len != len(data):
        data = b""  # Partial data is like no data !

    return data



def send_with_size(sock, bdata):
    if type(bdata) == str:
        bdata = bdata.encode()
    len_data = len(bdata)
    header_data = str(len_data).zfill(size_header_size - 1) + "|"

    bytea = header_data.encode() + bdata

    sock.send(bytea)

    if TCP_DEBUG and len_data > 0:
        print(f"\nSent({len_data})>>>{bytea[:LEN_TO_PRINT]}")



