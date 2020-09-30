from Utils import blist_to_bits


class BitField:

    def __init__(self, data):
        self.bits_str = blist_to_bits(data)
        self.dict = self.blist_dictionary(data)

    def has_piece(self, index):
        """ check whether bit field has an index """
        return self.dict.get(index, 0) == 1

    def length(self):
        """ get bitfield length """
        return len(self.dict)

    @staticmethod
    def blist_dictionary(blist):
        result = {}
        for index, value in enumerate(blist_to_bits(blist)):
            result[index] = int(value)

        return result

    def get_available_pieces(self):
        """ get set of available pieces """
        temp = set()
        for index, value in self.dict.items():
            if value == 1:
                temp.add(index)

        return temp

    def __str__(self):
        return f"<BitField()>"

    def __repr__(self):
        return self.__str__()


if __name__ == '__main__':

    field_data = b'\xFF'
    bitfield = BitField(field_data)
    assert bitfield.has_piece(0)
    assert bitfield.has_piece(7)
    assert not bitfield.has_piece(8)
