import asyncio
import sys
from Models import *


class Cli:

    def __init__(self, request_queue):
        self.request_queue = request_queue

    async def start(self):
        while True:
            inp = (await asyncio.get_event_loop()
                   .run_in_executor(None, sys.stdin.readline)).strip()

            if inp == "free":
                await self.free_pieces()
            elif inp == "pieces":
                await self.print_pieces()
            elif inp == 'metadata':
                await self.print_metadata()
            elif inp == 'trackers':
                await self.print_trackers()
            elif inp == 'peers':
                await self.print_peers()
            else:
                print('Got invalid command:', inp)
                print('Please enter one of the following: metadata, trackers, peers, pieces, free')

    async def free_pieces(self):
        self.request_queue.cancel_all()

    async def print_pieces(self):
        piece_hashes = self.request_queue.torrent.get_info().pieces()
        for key, value in self.request_queue.pieces.items():
            if value != RequestState.available:
                print('Piece', key, '(Current State:', value.value.capitalize() + ')')
                print('\tHash:', piece_hashes[key])

    async def print_metadata(self):
        print('Torrent Metadata:')

        torrent_file = {
            'announce': self.request_queue.torrent.get_announce(),
            'announce_list': self.request_queue.torrent.get_announce_list(),
            'creation date': self.request_queue.torrent.get_creation_date(),
            'comment': self.request_queue.torrent.get_comment(),
            'created by': self.request_queue.torrent.get_created_by(),
            'encoding': self.request_queue.torrent.get_encoding()
            }

        for key, value in torrent_file.items():
            if (value is not None):
                print('\t' + key + ' = ' + str(value))

        torrent_info = self.request_queue.torrent.get_info()
        torrent_info_dict = {
            'piece length': torrent_info.piece_length(),
            'pieces': str(torrent_info.piece_count()) + ' total\n\t\t(Use command \'pieces\' to view individual piece hashes.)',
            'private': torrent_info.private(),
            'name': torrent_info.file_name(),
            'length': torrent_info.file_length(),
            'md5sum': torrent_info.md5sum()
            }

        print('\tinfo =')
        for key, value in torrent_info_dict.items():
            if (value is not None):
                print('\t\t' + key + ' = ' + str(value))

    async def print_trackers(self):
        announce = self.request_queue.torrent.get_announce()
        announce_list = self.request_queue.torrent.get_announce_list()
        print('Trackers:')
        if (announce_list is not None):
            for i in range(0, len(announce_list)):
                print('\tTier', str(i + 1) + ':', announce_list[i])
        else:
            print('\t', announce)

    async def print_peers(self):
        if not self.request_queue.peers:
            print('No current peers.')
        else:
            print('Current Peers:')
            for peer in self.request_queue.peers:
                print('\t', peer.host + ':' + str(peer.port))
