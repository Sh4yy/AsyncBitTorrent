#!/usr/bin/python3

from Models import TorrentFile, RequestQueue
from Controllers import *
from Utils import create_bitfield
import asyncio
import argparse
import socket
import ipaddress


async def download_client(peer, torrent, request_queue):

    conn = ClientConnection(peer[0], peer[1], torrent, request_queue)

    try:
        conn.am_interested = True
        await conn.connect()
    except Exception as e:
        await conn.gracefully_shutdown()


def start_download(path):

    loop = asyncio.get_event_loop()
    torrent = TorrentFile(path)
    peer_data = Tracker(torrent).get_peers()

    peers = peer_data.get_peers()
    file_writer = FileWriter(torrent, loop)
    request_queue = RequestQueue(torrent, file_writer)

    print('File', torrent.get_info().file_name())
    print(f"Peers ({len(peers)})")

    loop.create_task(request_queue.print_progress())
    cli = Cli(request_queue)
    loop.create_task(cli.start())

    for peer in peers:
        print(f"Peer {peer[0]}:{peer[1]}")

    for peer in peers:
        loop.create_task(download_client(peer, torrent, request_queue))

    loop.run_until_complete(file_writer.worker())
    print('Done!!')


async def start_seeding(host, port, torrent_path, payload_path):

    torrent = TorrentFile(path=torrent_path)
    Tracker(torrent).get_peers(
        port=port, downloaded=torrent.get_info().file_length(),
        event='completed'
    )
    data = FileDivider.divide_file(
        payload_path, torrent.get_info().piece_length(),
        torrent.get_info().piece_count()
    )

    bitfield = create_bitfield(data, torrent.get_info().piece_count())

    async def seed_client(reader, writer):

        conn = SeedConnection(torrent, bitfield)
        host, port = writer.get_extra_info('peername')
        print(f'New Connection from {host}:{port}')

        try:
            await conn.start(reader, writer)
        except Exception as e:
            await conn.gracefully_shutdown()

    print(f'Listening on {host}:{port}')
    server = await asyncio.start_server(seed_client, host, port)
    await server.serve_forever()


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description="Setting up the BitTorrent Client's Argument Parser")
    parser.add_argument('-p', "--port", type=int, help="This is the host's port number.")
    parser.add_argument('-t', type=str, help="This is the path of the torrent file.")
    parser.add_argument('-a', type=str, choices=['download', 'seed'], help="This is the action being done.")
    parser.add_argument('-f', type=str, help="This is the path to the payload.")
    args = parser.parse_args()

    if args.a == "download":

        if args.t is None:
            print("missing path to the torrent file")
            exit()

        start_download(path=args.t)

    else:

        if not args.port or not args.f or not args.t:
            print('missing -p or -t or -f')
            exit()

        asyncio.get_event_loop().run_until_complete(
            start_seeding(
                host=ipaddress.IPv4Address(socket.INADDR_ANY).compressed,
                port=args.port,
                torrent_path=args.t,
                payload_path=args.f
            )
        )
