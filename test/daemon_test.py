import unittest
import time
import threading

from nose.tools import eq_, ok_
from os.path import isfile, exists, join
import shutil
from buoy.lib.daemon.daemon import Daemon


class DaemonTest(Daemon):
    def __init__(self, name, daemon_config):
        Daemon.__init__(self, name=name, daemon_config=daemon_config)
        self.nun_attempts = 0
        self.max_attempts = 4

    def run(self):
        while self.active:
            time.sleep(0.25)


class TestDaemon(unittest.TestCase):
    def setUp(self):
        self.path_pidfile = './pids/'
        self.name = 'DaemonTest'
        self.config = {
            'path_pidfile': self.path_pidfile
        }

        shutil.rmtree(self.path_pidfile)

    def test_should_createPathPID_when_noExits(self):
        self.daemon = Daemon(name=self.name, daemon_config=self.config)

        eq_(self.daemon.active, False)
        ok_(exists(self.config['path_pidfile']))

    def test_should_stopDaemon_when_callStopMethod(self):
        self.daemon = DaemonTest(name=self.name, daemon_config=self.config)
        t = threading.Thread(target=self.daemon.start)
        t.start()

        time.sleep(0.5)
        eq_(self.daemon.active, True)
        ok_(exists(join(self.path_pidfile, self.name + ".pid")))

        time.sleep(0.5)
        self.daemon.stop()

        eq_(self.daemon.active, False)
        ok_(exists(join(self.path_pidfile, self.name + ".pid")))

if __name__ == '__main__':
    unittest.main()
