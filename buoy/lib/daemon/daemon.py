"""Generic linux daemon base class for python 3.x."""

import logging
import time
import signal
import os
from os.path import isfile, exists

from functools import wraps
from buoy.lib.device.base import Device

logger = logging.getLogger(__name__)


class DaemonException(Exception):
    pass


class PID(object):
    def __init__(self, name, daemon_config):
        self.path_pidfile = daemon_config['path_pidfile']
        self.pid = str(os.getpid())
        self.name = name
        self.pidfile = os.path.join(self.path_pidfile, name + ".pid")
        self.create_path()

    def create_path(self):
        if not exists(self.path_pidfile):
            os.makedirs(self.path_pidfile)

    def create(self):
        if isfile(self.pidfile):
            raise DaemonException()

        f = open(self.pidfile, 'w')
        f.write(self.pid)
        f.close()

    def remove(self):
        os.remove(self.pidfile)


class Daemon(object):
    def __init__(self, name: str, daemon_config) -> None:
        self.status = True
        self.pidfile = PID(name, daemon_config)
        self.pidfile.create()

        signal.signal(signal.SIGINT, self.handler_signal)
        signal.signal(signal.SIGTERM, self.handler_signal)

    def handler_signal(self, signum, frame):
        self.status = False

    def before_stop(self):
        pass

    def stop(self):
        self.pidfile.remove()
        os._exit(os.EX_OK)


class DaemonDevice(Daemon):
    def __init__(self, device: Device, daemon_config) -> None:
        Daemon.__init__(self, device.name + "_device", daemon_config)
        self.device = device

    def _start(f):
        @wraps(f)
        def wrapped(self, *args, **kwargs):
            self.device.connect()
            f(self, *args, **kwargs)
            while self.status:
                time.sleep(2)

            self.before_stop()
            self.stop()

        return wrapped

    @_start
    def start(self):
        pass

    def before_stop(self):
        self.device.disconnect()
