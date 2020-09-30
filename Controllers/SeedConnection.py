import asyncio
from Utils import *
from Controllers.FileReader import FileReader


class SeedConnection:

    def __init__(self, torrent, bitfield):
        self.torrent = torrent
        self.reader = None
        self.writer = None
        self.peer_id = None
        self.bitfield = bitfield

        self.am_choking = True
        self.am_interested = False
        self.peer_choking = True
        self.peer_interested = False

    async def start(self, reader, writer):

        self.reader = reader
        self.writer = writer
        if not await self.receive_handshake():
            return await self.gracefully_shutdown()

        await self.send_bitfield()
        await self.send_unchoke()

        while True:
            await self._receive_socket()

    async def _receive_socket(self):

        try:
            length_data = await asyncio.wait_for(
                self.reader.read(4), timeout=0.5
            )
            if length_data == b'':
                return await self.gracefully_shutdown()
            length = unpack_length(length_data)
            if length == 0:
                return

            buff = b''
            while len(buff) < length:
                buff += await self.reader.read(length - len(buff))

            await self._process(length, buff[0:1], buff[1:])

        except asyncio.TimeoutError:
            pass

    async def send_bitfield(self):
        id = pack_id(5)
        length = pack_length(len(self.bitfield) + 1)
        await self._send(length + id + self.bitfield)

    async def send_unchoke(self):
        await self._send(pack_protocol_int(1) + pack_id(1))
        self.am_choking = False

    async def receive_handshake(self):

        length = ord(await self.reader.read(1))
        data = await self.reader.read(length + 8 + 20 + 20)
        pstr = data[0:length]
        reserved = data[length:length+8]
        info_hash = data[length+8:length+8+20]
        peer_id = data[length+8+20:length+8+40]

        if info_hash != self.torrent.get_info_hash():
            print('invalid info hash')
            return False

        self.peer_id = peer_id

        pstr_length = pack_id(19)
        pstr = 'BitTorrent protocol'.encode()
        reserved = (8 * chr(0)).encode()
        peer_id = self.torrent.peer_id().encode()

        await self._send(
            pstr_length + pstr + reserved + info_hash + peer_id
        )

        return True

    async def _send(self, data):
        """ send message to peer """
        self.writer.write(data)
        await self.writer.drain()

    async def _process(self, length, id, data):

        handlers = {
            0: self._handle_choke,
            1: self._handle_un_choke,
            2: self._handle_interested,
            3: self._handle_not_interested,
            4: self._handle_have,
            5: self._handle_bitfield,
            6: self._handle_request,
            7: self._handle_piece,
            8: self._handle_cancel,
            9: self._handle_port
        }

        id = ord(id)
        if id not in handlers:
            return

        await handlers.get(id)(length, data)

    async def _handle_choke(self, length, data):
        self.peer_choking = True

    async def _handle_un_choke(self, length, data):
        self.peer_choking = False

    async def _handle_interested(self, length, data):
        self.peer_interested = True

    async def _handle_not_interested(self, length, data):
        self.peer_interested = False

    async def _handle_have(self, length, data):
        pass

    async def _handle_bitfield(self, length, data):
        """ process bitfield """
        pass

    async def _handle_request(self, length, data):

        index_data = data[0:4]
        begin_data = data[4:8]
        length_data = data[8:12]

        index = unpack_protocol_int(index_data)
        begin = unpack_protocol_int(begin_data)
        length = unpack_protocol_int(length_data)

        block = await FileReader.read(index, begin, length)
        if block is None:
            return print('block is none')
        data = pack_id(7) + index_data + begin_data + block
        await self._send(pack_length(len(data)) + data)

    async def _handle_piece(self, length, data):
        """ process download response """
        pass

    async def _handle_cancel(self, length, data):
        pass

    async def _handle_port(self, length, data):
        pass

    async def gracefully_shutdown(self):
        print('Closing Connection')
        if self.writer is not None:
            try:
                await self.writer.wait_closed()
            except:
                pass
