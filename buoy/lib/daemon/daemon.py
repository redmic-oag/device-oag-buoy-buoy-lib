"""Generic linux daemon base class for python 3.x."""

import logging
import time
import signal
import os
from os.path import isfile, exists

from buoy.lib.device.base import Device

logger = logging.getLogger(__name__)


def get_config(device_name, buoy_config):
    serial_config = buoy_config['device'][device_name]['serial']
    db_config = buoy_config['database']
    service_config = buoy_config['service']

    return serial_config, db_config, service_config


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

        with open(self.pidfile, 'w') as f:
            f.write(self.pid)

    def remove(self):
        os.remove(self.pidfile)


class Daemon(object):
    def __init__(self, name: str, daemon_config) -> None:
        self.active = False
        self.pidfile = PID(name, daemon_config)

        signal.signal(signal.SIGINT, self.handler_signal)
        signal.signal(signal.SIGTERM, self.handler_signal)

    def handler_signal(self, signum, frame):
        self.active = False

    def _before_start(self):
        self.active = True
        self.pidfile.create()
        self.before_start()

    def before_start(self):
        """ Función que se ejecuta antes de iniciar el servicio """
        pass

    def start(self):
        self._before_start()
        self.run()
        self._stop()

    def run(self):
        """ Función donde implementar la lógica del servicio """
        pass

    def _before_stop(self):
        self.before_stop()

    def before_stop(self):
        """ Función que se ejecuta antes de parar el servicio """
        pass

    def _stop(self, code=os.EX_OK):
        self.active = False
        self._before_stop()
        self.pidfile.remove()
        os._exit(code)

    def stop(self):
        self._stop()

    def error(self):
        self._stop(os.EX_OSERR)


class DaemonDevice(Daemon):
    def __init__(self, device: Device, daemon_config) -> None:
        Daemon.__init__(self, device.name + "_device", daemon_config)
        self.device = device

    def before_start(self):
        self.connect()
        self.configure()

    def connect(self):
        self.device.connect()

    def configure(self):
        pass

    def run(self):
        while self.active:
            time.sleep(2)

    def before_stop(self):
        self.device.disconnect()


