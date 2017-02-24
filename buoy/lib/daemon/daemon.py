"""Generic linux daemon base class for python 3.x."""

import logging
import time
import signal
import os

from functools import wraps
from buoy.lib.device.base import Device

logger = logging.getLogger(__name__)


class Daemon(object):
    def __init__(self, device: Device) -> None:
        self.device = device
        self.status = True
        signal.signal(signal.SIGINT, self.kill)
        signal.signal(signal.SIGTERM, self.kill)

    def _start(f):
        @wraps(f)
        def wrapped(self, *args, **kwargs):
            self.device.connect()
            f(self, *args, **kwargs)
            while self.is_alive():
                time.sleep(2)

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




