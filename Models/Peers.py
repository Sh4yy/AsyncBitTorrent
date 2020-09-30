import bencode
from Utils import chunks, parse_host, parse_port


class Peers:

    def __init__(self, peer_data):
        self.peer_data = peer_data
        self.bn = bencode.decode(peer_data)

    def get_peers(self):
        """
        parse compact peers
        :returns: [(host, port)]
        """

        result = []
        for chunk in chunks(self.bn.get('peers'), 6):

            host = parse_host(chunk[0:4])
            port = parse_port(chunk[4:6])
            result.append((host, port))

        return result

    def __str__(self):
        return f"<Peers()>"

    def __repr__(self):
        return self.__str__()
