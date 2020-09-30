import asyncio
from concurrent.futures import ThreadPoolExecutor
import os, glob

_executor = ThreadPoolExecutor(10)


class FileReader:

    @classmethod
    async def read(cls, piece, offset, length):
        return await asyncio.get_event_loop().run_in_executor(
            _executor, cls._read,
            piece, offset, length
        )

    @staticmethod
    def _read(piece, offset, length):

        try:
            with open(f'pieces/{piece}', 'rb') as file:
                return file.read()[offset:offset + length]

        except Exception as e:
            print('error', e)


class FileDivider:

    @classmethod
    def divide_file(cls, path, chunks, total):
        
        files = glob.glob('pieces/*')
        for f in files:
            os.remove(f)
        
        field = {}
        i = 0
        with open(path, 'rb') as file:
            while i < total:
                data = file.read(chunks)
                if data == '':
                    break

                dst = open(f'pieces/{i}', 'wb')
                dst.write(data)
                dst.close()

                field[i] = True
                i += 1

        print('Done Dividing')
        return field
