import unittest

from buoy.tests.item_db_to_send_thread import DBToSendThreadTest
from buoy.tests.item import Item


class TestItemInDBToSendThread(DBToSendThreadTest):
    __test__ = True
    item_cls = Item


if __name__ == '__main__':
    unittest.main()
