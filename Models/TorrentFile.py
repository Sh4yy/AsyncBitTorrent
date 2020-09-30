from Utils import chunks
from hashlib import sha1
import bencode
import random
import string


class TorrentInfo:

    def __init__(self, info_bn):
        self.info_bn = info_bn
        pieces = self.info_bn.get('pieces')
        self.piece_arr = list(chunks(pieces, 20))

    def file_name(self):
        """ :returns: file name (single file mode) or directory name (multi-file mode) """
        return self.info_bn.get('name')

    def piece_length(self):
        """ :returns: number of bytes in each piece the file is split into """
        return self.info_bn.get('piece length')

    def pieces(self):
        """ :returns: list of 20 character sha1 hash """
        return self.piece_arr

    def private(self):
        """ :returns: integer 1 or 0; 0 if not present (optional) """
        try:
            return self.info_bn.get('private')
        except AttributeError:
            return 0

    def file_length(self):
        """ :returns: length of the file (single file mode), or None if not present (multi-file mode) """
        try:
            return self.info_bn.get('length')
        except AttributeError:
            return None

    def path(self):
        """ :returns: list of paths """
        return self.info_bn.get('path', None)

    def piece_count(self):
        """ :returns: number of pieces """
        return len(self.pieces())

    def md5sum(self):
        """ :returns: file's md5 hex digest, or None if not present (optional) """
        try:
            return self.info_bn.get('md5sum')
        except AttributeError:
            return None


class TorrentFile:

    _peer_id = ''.join(random.choices(string.ascii_letters + string.digits, k=20))

    def __init__(self, path):
        self.path = path
        self.data = open(path, 'rb').read()
        self.bn = bencode.decode(self.data)

    def get_announce(self):
        """ :returns: url of tracker """
        return self.bn.get('announce')

    def get_announce_list(self):
        """ :returns: 3d list of tracker urls in tiers, or None if not present (optional) """
        try:
            return self.bn.get('announce-list')
        except AttributeError:
            return None

    def get_creation_date(self):
        """ :returns: integer Unix time creation date, or None if not present (optional) """
        try:
            return self.bn.get('creation date')
        except AttributeError:
            return None

    def get_comment(self):
        """ :returns: string author comments, or None if not present (optional) """
        try:
            return self.bn.get('comment')
        except AttributeError:
            return None

    def get_created_by(self):
        """ :returns: string name/version of program that generated this file, or None if not present (optional) """
        try:
            return self.bn.get('created by')
        except AttributeError:
            return None

    def get_encoding(self):
        """ :returns: string encoding for piece hash dict, or None if not present (optional) """
        try:
            return self.bn.get('encoding')
        except AttributeError:
            return None

    def get_info(self):
        """ :returns: TorrentInfo instance """
        return TorrentInfo(self.bn.get('info'))

    def get_info_hash(self):
        """ :returns: create a hash from info """
        data = bencode.encode(self.bn.get('info'))
        return sha1(data).digest()

    @classmethod
    def peer_id(cls):
        """ return peer id """
        return cls._peer_id

    def __str__(self):
        return f"<Torrent(path={self.path})>"

    def __repr__(self):
        return self.__str__()
