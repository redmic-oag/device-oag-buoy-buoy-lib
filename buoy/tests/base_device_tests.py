import threading
import time
import unittest
from os import EX_OK, EX_OSERR
from unittest.mock import patch

from nose.tools import eq_
from serial import SerialException

import buoy.base.utils.config as load_config
from buoy.tests.database import prepare_db
from buoy.tests.serial import SerialMock


class BaseDeviceTest(unittest.TestCase):
    device_class = None
    DEVICE_NAME = None
    skip_test = False
    __test__ = False
    config_buoy_file = "tests/support/config/buoy.yaml"
    init_db = "tests/support/data/setup.sql"

    def setUp(self):
        if not self.__test__:
            self.skipTest("Skip BaseTest tests, it's a base class")

        buoy_config = load_config.load_config(path_config=self.config_buoy_file)
        buoy_config['database'] = prepare_db(sql=self.init_db)

        self.daemon = self.device_class(name=self.DEVICE_NAME, config=buoy_config)
        self.thread = threading.Thread(daemon=True, target=self.daemon.start)

    @patch('buoy.base.device.device.Serial', side_effect=SerialMock)
    def test_shouldReturnExitOK_when_stopService(self, mock_serial):
        self.thread.start()
        with self.assertRaises(SystemExit) as cm:
            time.sleep(1)
            self.daemon.stop()

        time.sleep(1)

        eq_(self.daemon.is_active(), False)
        prefix = '_thread_'
        names = ['reader', 'writer', 'save', 'send', 'reader_from_db']
        for name in names:
            field = prefix + name
            if hasattr(self.daemon, field):
                thread = getattr(self.daemon, field)
                is_active = getattr(thread, "is_active")()
                eq_(is_active, False, msg=("Thread %s is active" % (field,)))

        self.assertEqual(cm.exception.code, EX_OK)

    @patch('buoy.base.device.device.Serial', side_effect=SerialException())
    def test_shouldReturnException_when_theDeviceIsNotPresent(self, mock_serial):
        with self.assertRaises(SystemExit) as cm:
            time.sleep(1)
            self.daemon.start()

        self.assertEqual(cm.exception.code, EX_OSERR)


if __name__ == '__main__':
    unittest.main()
