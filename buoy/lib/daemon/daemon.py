"""Generic linux daemon base class for python 3.x."""

import logging
import time

from functools import wraps
from buoy.lib.device.base import Device

logger = logging.getLogger(__name__)


class Daemon(object):
    def __init__(self, device: Device) -> None:
        self.device = device

    def __start(self, f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            self.device.connect()
            f(*args, **kwargs)
            while True:
                time.sleep(5)

        return wrapped

    @__start
    def start(self):
        pass

    def stop(self):
        self.device.disconnect()

    def restart(self):
        self.stop()
        self.start()


