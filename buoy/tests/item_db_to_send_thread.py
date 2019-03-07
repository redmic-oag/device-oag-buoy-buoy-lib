import unittest
from os import path
from queue import Queue, Full
from unittest.mock import MagicMock

from nose.tools import eq_

from buoy.base.database import DeviceDB
from buoy.base.device.threads.resender import DBToSendThread
from buoy.tests.database import *

skip_test = False


class DBToSendThreadTest(unittest.TestCase):
    path_sql = 'tests/support/data'
    db_tablename = "device"
    item_cls = None

    @classmethod
    def setUpClass(cls):
        global skip_test

        if cls is DBToSendThreadTest:
            skip_test = True
        else:
            skip_test = False

        super(DBToSendThreadTest, cls).setUpClass()

    def setUp(self):
        if skip_test:
            self.skipTest("Skip BaseTest tests, it's a base class")

        db_conf = prepare_db(path.join(self.path_sql, 'setup.sql'))

        if not self.item_cls:
            print("Errorororor")

        self.dev_db = DeviceDB(
            db_config=db_conf,
            db_tablename=self.db_tablename,
            cls_item=self.item_cls
        )

    def test_noPutItemInQueue_when_queueIsFullInLoop(self):
        queue_notice = Queue()
        queue_send_data = Queue()
        queue_send_data.put_nowait = MagicMock(side_effect=Full())
        apply_sql_file(path.join(self.path_sql, 'data_example.sql'))

        thread = DBToSendThread(queue_send_data=queue_send_data, db=self.dev_db, queue_notice=queue_notice)

        thread.activity()

        eq_(queue_send_data.qsize(), 0)

    def test_putItemInQueue_when_queueIsFullInLoop(self):
        queue_notice = Queue()
        queue_send_data = Queue()
        apply_sql_file(path.join(self.path_sql, 'data_5_items_to_send.sql'))

        thread = DBToSendThread(queue_send_data=queue_send_data, db=self.dev_db, queue_notice=queue_notice)

        thread.activity()

        eq_(queue_send_data.qsize(), 5)


if __name__ == '__main__':
    unittest.main()
