import asyncio
from Utils import *
from Models import BitField
from asyncio import Queue
from Controllers.FileReader import FileReader


class ClientConnection:

    def __init__(self, host, port, torrent, request_queue):
        self.host = host
        self.port = port
        self.torrent = torrent
        self.request_queue = request_queue
        self.writer = None
        self.reader = None
        self.bitfield = None
        self.send_queue = Queue()

        self.am_choking = True
        self.am_interested = False
        self.peer_choking = True
        self.peer_interested = False

        self.required_index = None
        self.request_queue.register_peer(self)

    async def connect(self):
        """ start a connection with peer """

        self.reader, self.writer = await asyncio.open_connection(
            host=self.host,
            port=self.port
        )

        await self.send_handshake()
        await self.reader.read(68)
        await self.send_unchoke()

        while True:
            await self._receive_socket()
            await self._send_socket()
            if not self.peer_choking and self.bitfield and self.am_interested:
                await self.send_request()

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

    async def send_unchoke(self):
        await self._send(pack_protocol_int(1) + pack_id(1))
        self.am_choking = False

    async def _send_socket(self):

        try:
            message = self.send_queue.get_nowait()
            await self._send(message)
        except asyncio.QueueEmpty:
            pass

    async def queue_available(self, piece_handler):

        index = piece_handler.piece
        id = pack_id(4)
        piece = pack_protocol_int(index)
        data = id + piece
        length = pack_protocol_int(len(data))
        self.send_queue.put_nowait(length + data)

    async def send_handshake(self):
        """ send handshake to peer """

        pstr_length = pack_id(19)
        pstr = 'BitTorrent protocol'.encode()
        reserved = (8 * chr(0)).encode()
        info_hash = self.torrent.get_info_hash()
        peer_id = self.torrent.peer_id().encode()

        await self._send(
            pstr_length + pstr + reserved + info_hash + peer_id
        )

    async def send_request(self):

        if self.required_index is None:
            self.required_index = self.request_queue.get_request(self.bitfield)
            if self.required_index is None:
                return

        if self.required_index.is_complete():
            await self.request_queue.confirm_download(self.required_index)
            # write piece to file
            self.required_index = None
            return await self.send_request()

        piece_data = self.required_index.next_piece()
        while piece_data is not None:

            piece, offset, length = piece_data

            id = pack_id(6)
            index = pack_protocol_int(piece)
            begin = pack_protocol_int(offset)
            length = pack_protocol_int(length)

            data = id + index + begin + length
            data = pack_length(len(data)) + data

            await self._send(data)
            piece_data = self.required_index.next_piece()

    async def send_interested(self):

        data = pack_length(1) + pack_id(2)
        await self._send(data)

    async def _process(self, length, id, data):
        """ process each incoming message """

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

        # print('got', id, handlers.get(id).__name__)
        await handlers.get(id)(length, data)

    async def _handle_choke(self, length, data):
        self.peer_choking = True
        print('peer choking')
        await self.gracefully_shutdown()

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
        self.bitfield = BitField(data)
        await self.send_interested()

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

        index_data = data[0:4]
        begin_data = data[4:8]
        block = data[8:]

        index = unpack_protocol_int(index_data)
        begin = unpack_protocol_int(begin_data)

        self.required_index.received(index, begin, block)

    async def _handle_cancel(self, length, data):
        pass

    async def _handle_port(self, length, data):
        pass

    async def _send(self, data):
        """ send message to peer """
        self.writer.write(data)
        await self.writer.drain()

    async def gracefully_shutdown(self):
        # print('shutting down peer')
        if self.required_index is not None:
            self.request_queue.cancel_piece(self.request_queue)

        if self.writer is not None:
            try:
                await self.writer.wait_closed()
            except:
                pass

        if self.request_queue is not None:
            self.request_queue.remove_peer(self)
            self.request_queue = None
