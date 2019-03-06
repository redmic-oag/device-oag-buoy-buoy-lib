from unittest.mock import MagicMock


class SerialMock(object):
    def __init__(self, **kwargs):
        self.read = MagicMock(return_value=b'Hola')
        self.in_waiting = MagicMock(return_value=4)
        self.write = MagicMock()
        self.close = MagicMock()
        self.is_open = MagicMock(return_value=True)
