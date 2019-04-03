import unittest
from datetime import datetime, timezone
from buoy.tests.item_save_thread import ItemSaveThreadTest
from buoy.tests.item import Item


def get_item():
    data = {
        'date': datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f%z"),
        'value': '26.8'
    }
    return Item(**data)


class TestItemSaveThread(ItemSaveThreadTest):
    __test__ = True


if __name__ == '__main__':
    unittest.main()
