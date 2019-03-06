# -*- coding: utf-8 -*-

import logging
import time
from queue import Queue
from threading import Thread

from serial import Serial

logger = logging.getLogger(__name__)


class BaseThread(Thread):
    def __init__(self, queue_notice: Queue, **kwargs):
        self.timeout_wait = kwargs.pop('timeout_wait', 0.2)
        super(BaseThread, self).__init__(**kwargs)
        self.active = False
        self.queue_notice = queue_notice

    def run(self):
        logging.info("Start thread %s", self.__class__.__name__)
        self.before_activity()
        self.active = True
        while self.is_active():
            self.activity()
            time.sleep(self.timeout_wait)
        self.after_activity()

    def is_active(self) -> bool:
        """
        Retorna el estado del hilo, activo o parado

        :return: Estado del hilo
        """
        return self.active

    def before_activity(self):
        pass

    def after_activity(self):
        pass

    def activity(self):
        """
        Función donde implementar el proceso a ejecutar el hilo
        :return:
        """
        pass

    def stop(self):
        """ Para el hilo """
        self.active = False
        logging.info("Stop thread %s", self.__class__.__name__)

    def error(self, exception):
        self.queue_notice.put_nowait(exception)
        self.stop()


class DeviceBaseThread(BaseThread):
    def __init__(self, device: Serial, queue_notice: Queue, **kwargs):
        super(DeviceBaseThread, self).__init__(queue_notice)
        self.device = device

    def is_active(self):
        return super().is_active() and self.device.is_open
