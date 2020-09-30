from asyncio import Queue
import os, glob
from concurrent.futures import ThreadPoolExecutor


_executor = ThreadPoolExecutor(10)


class FileWriter:

    def __init__(self, torrent, loop):
        self.queue = Queue()
        self.torrent = torrent
        self.loop = loop
        self.path = torrent.get_info().file_name()
        self.is_done = False
        self.memory = {}

        files = glob.glob('pieces/*')
        for f in files:
            os.remove(f)

    def add_piece(self, piece):
        self.queue.put_nowait(piece)

    async def worker(self):
        while not self.is_done or not self.queue.empty():
            piece = await self.queue.get()

            await self._write_piece(piece)
            self.queue.task_done()

        await self._combine_pieces()
        self.loop.stop()

    async def _write_piece(self, piece):

        await self.loop.run_in_executor(
            _executor, self._writer,
            piece.piece, piece.get_data()
        )

        self.memory[piece.piece] = True

    async def _combine_pieces(self):

        with open(self.path, 'wb') as dest:
            keys = list(sorted(self.memory.keys()))
            for key in keys:
                src = open(f'pieces/{key}', 'rb').read()
                dest.write(src)

        files = glob.glob('pieces/*')
        for f in files:
            os.remove(f)

    def _writer(self, piece, data):

        file = open(f'pieces/{piece}', 'wb')
        file.write(data)
        file.close()

    async def finish_writing(self):
        self.is_done = True
        print('\nWriting to file')
