import unittest
from queue import Queue

from nose.tools import eq_

from buoy.base.device.threads.base import BaseThread


class TestThreadBase(unittest.TestCase):
    def setUp(self):
        queue_notice = Queue()
        self.thread = BaseThread(queue_notice=queue_notice)

    def test_is_aliveReturnFalse_when_createThread(self):
        eq_(self.thread.is_alive(), False)

    def test_is_aliveReturnFalse_when_stopThread(self):
        self.thread.active = True

        self.thread.stop()
        eq_(self.thread.is_alive(), False)


if __name__ == '__main__':
    unittest.main()
