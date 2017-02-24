"""Generic linux daemon base class for python 3.x."""

import logging
import time
import signal
import os
from os.path import isfile

from functools import wraps
from buoy.lib.device.base import Device

logger = logging.getLogger(__name__)


class DaemonException(Exception):
    pass


class PID(object):
    def __init__(self, name, **kwargs):
        self.path_pidfile = kwargs.pop('path_pidfile', '/var/run/')
        self.pid = str(os.getpid())
        self.name = name
        self.pidfile = os.path.join(self.path_pidfile, name + ".pid")

    def create(self):
        if isfile(self.pidfile):
            raise DaemonException()

        f = open(self.pidfile, 'w')
        f.write(self.pid)
        f.close()

    def remove(self):
        os.remove(self.pidfile)


class Daemon(object):
    def __init__(self, device: Device) -> None:
        self.device = device
        self.status = True
        self.pidfile = PID(device.name)
        signal.signal(signal.SIGINT, self.kill)
        signal.signal(signal.SIGTERM, self.kill)

    def _start(f):
        @wraps(f)
        def wrapped(self, *args, **kwargs):
            self.pidfile.create()
            self.device.connect()
            f(self, *args, **kwargs)
            while self.is_alive():
                time.sleep(2)

            self.pidfile.remove()
            os._exit(os.EX_OK)

        return wrapped

    @_start
    def start(self):
        pass

    def is_alive(self):
        return self.status

    def kill(self, signum, frame):
        self.device.disconnect()
        self.status = False




