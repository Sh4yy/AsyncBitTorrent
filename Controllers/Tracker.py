import requests
from Models.Peers import Peers


"""
following this article
https://wiki.theory.org/index.php/BitTorrentSpecification#Tracker_HTTP.2FHTTPS_Protocol
"""


class Tracker:

    def __init__(self, torrent):
        """
        initialize a new Tracker
        :param torrent: torrent file instance
        """
        self.torrent = torrent

    def get_peers(self, port=433, downloaded=0, event='started'):

        params = {
            'info_hash': self.torrent.get_info_hash(),
            'peer_id': self.torrent.peer_id(),
            'port': port,
            'compact': 1,
            'event': event,
            'uploaded': 0,
            'downloaded': downloaded,
            'left': self.torrent.get_info().file_length() - downloaded
        }

        url = self.torrent.get_announce()
        res = requests.get(url, params=params)
        res.raise_for_status()
        return Peers(res.content)
