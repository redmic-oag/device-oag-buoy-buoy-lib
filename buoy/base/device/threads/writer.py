# -*- coding: utf-8 -*-

import logging
from queue import Queue, Empty

from serial import Serial, SerialException

from buoy.base.device.exceptions import LostConnectionException
from buoy.base.device.threads.base import DeviceBaseThread

logger = logging.getLogger(__name__)


class DeviceWriter(DeviceBaseThread):
    """ Clase encargada de enviar datos al dispositivo """

    def __init__(self, device: Serial, queue_write_data: Queue, queue_notice: Queue):
        super(DeviceWriter, self).__init__(device, queue_notice)
        self.queue_write_data = queue_write_data

    def activity(self):
        try:
            data = self.queue_write_data.get(timeout=self.timeout_wait)
            self.device.write(data.encode())
            logger.info("Write data in device - " + data)
            self.queue_write_data.task_done()
        except SerialException as ex:
            logger.error("Device disconnected")
            self.error(LostConnectionException(exception=ex))
        except Empty:
            pass
