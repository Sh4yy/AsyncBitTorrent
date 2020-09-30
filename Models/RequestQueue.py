from enum import Enum
import random
import asyncio
import math
from hashlib import sha1
from time import time
from Models.ProgressBar import print_progress_bar


class RequestState(Enum):
    required = 'required'
    available = 'available'
    downloading = 'downloading'
    race = 'race'


class RequestQueue:
    """
    the task of this class is to keep track of
    required pieces for a torrent file
    """

    def __init__(self, torrent, file_writer):
        """ initialize a new queue """
        self.torrent = torrent
        self.pieces = {}
        self.file_writer = file_writer
        self.peers = []

        self.last_percent = None
        self.last_update = None

        for i in range(torrent.get_info().piece_count()):
            self.pieces[i] = RequestState.required

    def _get_required_pieces(self):
        """ get set of remaining pieces """
        temp = set()
        for key, value in self.pieces.items():
            if value == RequestState.required or value == RequestState.race:
                temp.add(key)

        return temp

    def register_peer(self, peer):
        if peer not in self.peers:
            self.peers.append(peer)

    def remove_peer(self, peer):
        if peer in self.peers:
            self.peers.remove(peer)

    def get_request(self, bitfield):
        """
        cross match a required index with peer's bitfield
        """

        required = self._get_required_pieces()
        available = bitfield.get_available_pieces()
        intersect = required.intersection(available)

        if len(intersect) == 0:
            return None

        value = random.choice(list(intersect))
        piece_length = self.torrent.get_info().piece_length()
        file_size = self.torrent.get_info().file_length()
        piece_length = min(file_size - (value * piece_length), piece_length)

        if self.pieces[value] != RequestState.race:
            self.pieces[value] = RequestState.downloading
        return PieceHandler(value, piece_length)

    def cancel_piece(self, index):
        """ for when a peer fails to deliver a piece """

        if self.pieces.get(index) == RequestState.downloading:
            self.pieces[index] = RequestState.required

    def cancel_all(self):
        for key in self.pieces.keys():
            self.cancel_piece(key)

    async def confirm_download(self, piece_handler):
        """ confirm downloaded piece """

        if self.is_finished():
            return

        state = self.pieces.get(piece_handler.piece)
        if state == RequestState.downloading or state == RequestState.race:
            if self._verify_piece(piece_handler):
                self.pieces[piece_handler.piece] = RequestState.available
                self.file_writer.add_piece(piece_handler)
                await self.write_available(piece_handler)
            else:
                self.pieces[piece_handler.piece] = RequestState.required

        if self.is_finished():
            await self.finalize_download()

    async def write_available(self, piece_handler):
        for peer in self.peers:
            if peer is None:
                continue
            await peer.queue_available(piece_handler)

    def _verify_piece(self, piece_handler):
        piece_hash = piece_handler.create_hash()
        expected_hash = self.torrent.get_info().pieces()[piece_handler.piece]
        return piece_hash == expected_hash

    async def finalize_download(self):
        await self.single_progress()
        await self.file_writer.finish_writing()
        for peer in self.peers:
            await peer.gracefully_shutdown()

    def is_finished(self):
        """ check whether all the pieces have been downloaded """
        for key, value in self.pieces.items():
            if value != RequestState.available:
                return False
        return True

    async def print_progress(self):

        while True:

            progress = await self.single_progress()
            await self.block_check(progress)
            await asyncio.sleep(0.2)

    async def single_progress(self):

        finished = 0
        for key, value in self.pieces.items():
            if value == RequestState.available:
                finished += 1

        tot_len = len(self.pieces)
        progress = float(finished) / float(tot_len)
        file_len = self.torrent.get_info().file_length() or 0
        mb = float(file_len * progress) / (1000 * 1000)
        if progress * 100 <= 100:
            print_progress_bar(progress * 100, mb, len(self.peers))

        return progress

    async def block_check(self, progress):

        if self.last_percent == progress and progress > 0.0:
            if time() - self.last_update > 10:
                self.cancel_all()

        else:
            self.last_percent = progress
            self.last_update = time()


class PieceHandler:

    MAX_SIZE = 16000
    MAX_IN_FLIGHT = 10

    def __init__(self, piece, length):
        self.piece = piece
        self.length = length
        self.data = {}
        self.status = {}
        self._populate_data()
        self.req_count = 0

    def _populate_data(self):
        """ populate expected indices """
        block_count = math.ceil(float(self.length) / float(self.MAX_SIZE))
        for block_index in range(block_count):
            self.data[block_index * self.MAX_SIZE] = None
            self.status[block_index * self.MAX_SIZE] = RequestState.required

    def is_complete(self):
        for value in self.status.values():
            if value != RequestState.available:
                return False

        return True

    def received(self, index, begin, block):
        if not index == self.piece:
            return print('invalid piece', self.piece, index)

        if begin not in self.data:
            return print('invalid block', begin)

        if self.status[begin] != RequestState.downloading:
            return print('invalid request state', self.status[begin])

        self.data[begin] = block
        self.status[begin] = RequestState.available
        self.req_count -= 1

    def next_length(self, index):
        return min(self.MAX_SIZE, self.length - index)

    def next_piece(self):
        """
        get next block within this piece
        :returns: (piece index, offset within piece, length of block)
        """
        if self.req_count > self.MAX_IN_FLIGHT:
            return None

        for offset, value in self.status.items():
            if value == RequestState.required:
                self.req_count += 1
                self.status[offset] = RequestState.downloading
                return self.piece, offset, self.next_length(offset)
        return None

    def get_data(self):
        total = b''
        for key in sorted(self.data.keys()):
            total += self.data.get(key)

        return total

    def create_hash(self):
        return sha1(self.get_data()).digest()

    def __str__(self):
        return f"<PieceHandler(piece={self.piece})>"

    def __repr__(self):
        return self.__str__()