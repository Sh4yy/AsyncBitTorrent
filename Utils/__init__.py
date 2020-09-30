import struct
import ipaddress


def chunks(list, n):
    for i in range(0, len(list), n):
        yield list[i:i + n]


def parse_host(data):
    return ipaddress.IPv4Address(data).compressed


def parse_port(data):
    return struct.unpack('!H', data)[0]


def unpack_length(data):
    return struct.unpack('!L', data)[0]


def pack_length(length):
    return struct.pack('!L', length)


def pack_protocol_int(num):
    return struct.pack('!I', num)


def unpack_protocol_int(num):
    return struct.unpack('!I', num)[0]


def pack_id(id):
    return struct.pack('!B', id)


def byte_to_bit(b):
    return bin(int(b, 16))[2:].zfill(8)


def blist_to_bits(blist):
    result = ''
    for i in chunks(blist.hex(), 2):
        result += byte_to_bit(i)

    return result


def create_bits(data, piece_count):
    b = ''
    for i in range(piece_count):
        b += '1' if data.get(i, False) else '0'

    pieces = list(chunks(b, 8))
    result = []
    for piece in pieces:
        result.append(piece[::-1].zfill(8)[::-1])

    return ''.join(result)


def hex_from_bits(bits):
    return bytes.fromhex(hex(int(bits, 2))[2:])


def create_bitfield(data, piece_count):
    bits = create_bits(data, piece_count)
    return hex_from_bits(bits)


