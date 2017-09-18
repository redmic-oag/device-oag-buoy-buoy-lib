# -*- coding: utf-8 -*-

import logging
import time
import signal
import sys
from os import getpid, makedirs, remove, EX_OK, EX_OSERR, kill
from os.path import isfile, exists, join

from buoy.lib.device.exceptions import DeviceBaseException
from buoy.lib.notification.common import Notification, NotificationLevel, NoticeBase

logger = logging.getLogger(__name__)


def get_config(device_name, buoy_config):
    serial_config = buoy_config['device'][device_name]['serial']
    db_config = buoy_config['database']
    service_config = buoy_config['service']

    return serial_config, db_config, service_config


class DaemonException(Exception):
    pass


class PID(object):
    """
        Clase para la gestión del PID de un servicio utilizando un fichero
    """
    def __init__(self, daemon_name, daemon_config):
        self.path_pidfile = daemon_config['path_pidfile']
        self.pid = getpid()
        self.daemon_name = daemon_name
        self.pid_file = join(self.path_pidfile, self.daemon_name + ".pid")
        self.create_path_pid_file()

    def create_path_pid_file(self):

        if not exists(self.path_pidfile):
            makedirs(self.path_pidfile)

    def create_pid_file(self):
        if isfile(self.pid_file):
            remove(self.pid_file)

        with open(self.pid_file, 'w') as f:
            f.write(str(self.pid))

    def remove_pid_file(self):
        if isfile(self.pid_file):
            remove(self.pid_file)


class Daemon(PID):
    """
        Clase base para la creación de un servicio linux
        Cuenta con un ciclo de vida:
            * before_start
            * start
            * run
            * before_stop
            * stop
    """
    def __init__(self, daemon_name: str, daemon_config, **kwargs) -> None:
        super(Daemon, self).__init__(daemon_name, daemon_config)
        self.active = False
        self.daemon_name = daemon_name
        self.start_timeout = kwargs.pop('start_timeout', 0)

        signal.signal(signal.SIGINT, self.handler_signal)
        signal.signal(signal.SIGTERM, self.handler_signal)

    def handler_signal(self, signum, frame):
        """ Maneja la captura de señales de interrupción, poniendo el servicio en modo inactivo """
        self.active = False

    def _before_start(self):
        self.active = True
        self.create_pid_file()
        self.before_start()

    def before_start(self):
        """ Función que se ejecuta antes de iniciar el servicio """
        pass

    def start(self):
        self.send_notification(Notification(message="Start service %s" % self.daemon_name,
                                            level=NotificationLevel.HIGHT))
        self._before_start()
        time.sleep(self.start_timeout)
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

    def _stop(self, code=EX_OK):
        self.send_notification(Notification(message="Stop service %s" % self.daemon_name,
                                            level=NotificationLevel.HIGHT))

        self.active = False
        self._before_stop()
        time.sleep(0.5)
        kill(self.pid, signal.SIGUSR1)
        self.remove_pid_file()
        sys.exit(code)

    def stop(self):
        self._stop()

    def error(self):
        """ Función que se ejecuta cuando se produce un error """
        self.send_notification(Notification(message="Error in service %s" % self.daemon_name,
                                            level=NotificationLevel.HIGHT))
        self._stop(code=EX_OSERR)

    def send_notification(self, notification: NoticeBase):
        logger.info(notification.message)


class DaemonDevice(Daemon):
    def __init__(self, daemon_name: str, daemon_config) -> None:
        Daemon.__init__(self, daemon_name=daemon_name, daemon_config=daemon_config)

    def before_start(self):
        try:
            self.connect()
        except DeviceBaseException as ex:
            self.send_notification(Notification(message=ex.message, level=ex.level, datetime=ex.datetime))
        except Exception as ex:
            pass

        self.error()

    def connect(self):
        pass

    def run(self):
        while self.active:
            time.sleep(0.2)

    def before_stop(self):
        self.disconnect()


