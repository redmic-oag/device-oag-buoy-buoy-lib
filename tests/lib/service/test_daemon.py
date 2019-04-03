import os
import shutil
import signal
import threading
import time
import unittest
from os.path import exists, join
from unittest.mock import patch

from nose.tools import eq_, ok_

from buoy.base.service.daemon import Daemon


class DaemonTest(Daemon):
    def __init__(self, daemon_name, daemon_config):
        super(DaemonTest, self).__init__(daemon_name=daemon_name, daemon_config=daemon_config)
        self.nun_attempts = 0
        self.max_attempts = 4

    def run(self):
        while self.is_active():
            time.sleep(0.01)


class TestDaemon(unittest.TestCase):
    def setUp(self):
        self.path_pidfile = './tests/support/pids/'
        self.name = 'DaemonTest'
        self.config = {
            'path_pidfile': self.path_pidfile
        }

        # Limpia el directorio donde se almacenan los PID
        if exists(self.path_pidfile):
            shutil.rmtree(self.path_pidfile)

    def run_daemon_in_thread(self):
        self.daemon = DaemonTest(daemon_name=self.name, daemon_config=self.config)
        t = threading.Thread(target=self.daemon.start)
        t.start()

    def test_should_createPathPID_when_noExits(self):
        self.daemon = Daemon(daemon_name=self.name, daemon_config=self.config)

        eq_(self.daemon.is_active(), False)
        eq_(self.daemon.daemon_name, self.name)
        ok_(exists(self.config['path_pidfile']))

    @patch.object(Daemon, '_before_start', return_value=None)
    @patch.object(Daemon, 'run', return_value=None)
    @patch.object(Daemon, '_stop', return_value=None)
    def test_should_lifecycle_when_callStart(self, mock_stop, mock_run, mock_before_start):
        self.daemon = Daemon(daemon_name=self.name, daemon_config=self.config)
        self.daemon.start()

        eq_(self.daemon.is_active(), False)
        eq_(mock_before_start.call_count, 1)
        eq_(mock_run.call_count, 1)
        eq_(mock_stop.call_count, 1)

    def test_should_stopDaemonAndCleanPIDFile_when_callStopMethod(self):
        self.run_daemon_in_thread()

        time.sleep(0.2)
        eq_(self.daemon.is_active(), True)
        ok_(exists(join(self.path_pidfile, self.name + ".pid")))

        time.sleep(0.2)
        with self.assertRaises(SystemExit) as cm:
            self.daemon.stop()

        self.assertEqual(cm.exception.code, 0)

        eq_(self.daemon.is_active(), False)
        ok_(not exists(join(self.path_pidfile, self.name + ".pid")))

    # TODO Arreglar tests
    @unittest.skip
    def test_should_stopDaemonAndCleanPIDFile_when_sendSignalSIGINT(self):
        self.run_daemon_in_thread()
        eq_(self.daemon.is_active(), True)

        time.sleep(0.2)
        os.kill(self.daemon.pid, signal.SIGINT)

        eq_(self.daemon.is_active(), False)

    @unittest.skip
    def test_should_stopDaemonAndCleanPIDFile_when_sendSignalSIGTERM(self):
        self.run_daemon_in_thread()
        eq_(self.daemon.is_active(), True)

        time.sleep(0.2)
        os.kill(self.daemon.pid, signal.SIGTERM)

        eq_(self.daemon.is_active(), False)

    @patch.object(Daemon, 'is_active', return_value=True)
    def test_should_exitWithCode0_when_callStop(self, mock_is_active):
        self.daemon = Daemon(daemon_name=self.name, daemon_config=self.config)

        with self.assertRaises(SystemExit) as cm:
            self.daemon.stop()

        self.assertEqual(cm.exception.code, os.EX_OK)

    @patch.object(Daemon, 'is_active', return_value=True)
    def test_should_exitWithCode1_when_callError(self, mock_is_active):
        self.daemon = Daemon(daemon_name=self.name, daemon_config=self.config)

        with self.assertRaises(SystemExit) as cm:
            self.daemon.error()

        self.assertEqual(cm.exception.code, os.EX_OSERR)


if __name__ == '__main__':
    unittest.main()
