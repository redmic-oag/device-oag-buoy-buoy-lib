import threading
import unittest
from os import EX_OK, EX_OSERR
from unittest.mock import patch

import time
from nose.tools import eq_
from serial import SerialException

import buoy.lib.utils.config as load_config
from test.support.function.database import prepare_db
from test.support.mock.SerialMock import SerialMock

config_buoy_file = "test/support/config/buoy.yaml"
config_log_file = "test/support/config/logging.yaml"


class BaseDeviceTest(unittest.TestCase):
    device_class = None
    DEVICE_NAME = None
    skip_test = False
    __test__ = False

    def setUp(self):
        if not self.__test__:
            self.skipTest("Skip BaseTest tests, it's a base class")

        buoy_config = load_config.load_config(path_config=config_buoy_file)
        buoy_config['database'] = prepare_db()

        self.daemon = self.device_class(name=self.DEVICE_NAME, buoy_config=buoy_config)
        self.thread = threading.Thread(daemon=True, target=self.daemon.start)

    @unittest.skip("Hay que corregirlo")
    @patch('buoy.client.device.common.base.Serial', side_effect=SerialMock)
    def test_shouldReturnExitOK_when_stopService(self, mock_serial):
        self.thread.start()
        with self.assertRaises(SystemExit) as cm:
            time.sleep(1)
            self.daemon.stop()

        eq_(self.daemon.is_active(), False)
        prefix = '_thread_'
        names = ['reader', 'writer', 'save', 'send']
        for name in names:
            field = prefix + name
            if hasattr(self.daemon, field):
                thread = getattr(self.daemon, field)
                is_active = getattr(thread, "is_active")()
                eq_(is_active, False, msg=("Thread %s is active" % (field,)))

        self.assertEqual(cm.exception.code, EX_OK)

    @patch('buoy.client.device.common.base.Serial', side_effect=SerialException())
    def test_shouldReturnException_when_theDeviceIsNotPresent(self, mock_serial):
        with self.assertRaises(SystemExit) as cm:
            time.sleep(1)
            self.daemon.start()

        self.assertEqual(cm.exception.code, EX_OSERR)


if __name__ == '__main__':
    unittest.main()
