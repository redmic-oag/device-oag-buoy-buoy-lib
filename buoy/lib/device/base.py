# -*- coding: utf-8 -*-

import logging
import time
from queue import Queue
from threading import Thread

from serial import Serial, SerialException

from buoy.lib.notification.common import Notification, NotificationLevel, NoticeData, NoticeBase
from buoy.lib.notification.client.device import NoticeQueue
from buoy.lib.device.exceptions import LostConnectionException, DeviceNoDetectedException
from buoy.lib.device.database import DeviceDB


logger = logging.getLogger(__name__)


class DeviceReader(Thread):
    """ Clase encargada de leer y parsear los datos que devuelve el dispositivo """
    def __init__(self, device, queue_save_data: Queue, queue_notice: NoticeQueue, queue_exceptions: Queue):
        Thread.__init__(self)
        self.device = device
        self.queue_save_data = queue_save_data
        self.queue_notice = queue_notice
        self.queue_exceptions = queue_exceptions

    def run(self):
        buffer = ''
        first_item = True
        while self.device.isOpen:
            try:
                buffer += self.device.read(self.device.inWaiting()).decode()
                if '\n' in buffer:
                    lines = buffer.split('\n')

                    for line in lines:
                        if len(line):
                            item = self.parser(line)
                            if item:
                                self.queue_save_data.put_nowait(item)
                                if first_item:
                                    first_item = False
                                    self.queue_notice.put_nowait(Notification(message=line,
                                                                              level=NotificationLevel.HIGHT))

                            logger.info("Received data - " + line)

                    buffer = ''

            except (OSError, Exception) as ex:
                self.queue_exceptions.put_nowait(LostConnectionException(exception=ex))
                break

            time.sleep(0.5)

    def parser(self, data):
        pass


class DeviceWriter(Thread):
    """ Clase encargada de enviar datas al dispositivo """
    def __init__(self, device, queue_write_data: Queue, queue_exceptions: Queue):
        Thread.__init__(self)
        self.device = device
        self.queue_write_data = queue_write_data
        self.queue_exceptions = queue_exceptions

    def run(self):
        while self.device.isOpen:
            data = self.queue_write_data.get()
            try:
                self.device.write(data.encode())
                time.sleep(1)
            except SerialException as ex:
                self.queue_exceptions.put_nowait(LostConnectionException(exception=ex))
            finally:
                logger.info("Send - " + data)
                self.queue_write_data.task_done()


class ItemSaveThread(Thread):
    def __init__(self, db: DeviceDB, queue_save_data: Queue, queue_notice: NoticeQueue):
        Thread.__init__(self)
        self.db = db
        self.queue_save_data = queue_save_data
        self.queue_notice = queue_notice

    def run(self):
        while True:
            item = self.queue_save_data.get()
            if not item:
                break

            item = self.save(item)
            data = NoticeData(device='ACMPlus', data=item)
            self.queue_notice.put_nowait(data)
            self.queue_save_data.task_done()

    def save(self, item):
        """ Guarda en la base de datos """
        return self.db.save(item)


class Device(object):
    def __init__(self, device_name: None, **kwargs):
        self.serial_config = kwargs.pop('serial_config', None)
        self.db = kwargs.pop('db')
        self.cls_reader = kwargs.pop('cls_reader', DeviceReader)

        self.active = False

        # Device
        self.name = device_name
        self._dev_connection = None

        if not hasattr(self, 'queues'):
            self.queues = {}

        for queue_name in ['exceptions']:
            self.queues[queue_name] = Queue()

    def connect(self):
        self.send_notification(Notification(message="Connecting to device", level=NotificationLevel.NORMAL))
        try:
            self._dev_connection = Serial(**self.serial_config)
        except SerialException as ex:
            raise DeviceNoDetectedException(process=self.name, exception=ex)

        if self.is_open():
            self.send_notification(Notification(message="Connected to device", level=NotificationLevel.NORMAL))

            for queue_name in ['write_data', 'save_data']:
                self.queues[queue_name] = Queue()

            self._create_threads()

            self._thread_reader.start()
            self._thread_writer.start()
            self._thread_save.start()

            self.configure()

            self._listener_exceptions()

    def configure(self):
        pass

    def _listener_exceptions(self):
        while self.active:
            ex = self.queues['exceptions'].get()
            raise ex

    def _create_threads(self):
        self._thread_reader = self.cls_reader(device=self._dev_connection,
                                              queue_save_data=self.queues['save_data'],
                                              queue_exceptions=self.queues['exceptions'],
                                              queue_notice=self.queues['notice'])

        self._thread_writer = DeviceWriter(device=self._dev_connection,
                                           queue_write_data=self.queues['write_data'],
                                           queue_exceptions=self.queues['exceptions'],
                                           )

        self._thread_save = ItemSaveThread(queue_save_data=self.queues['save_data'],
                                           queue_notice=self.queues['notice'],
                                           db=self.db)

    def disconnect(self):
        if self.is_open():
            self._dev_connection.close()
            self.send_notification(Notification(message="Disconnected to device", level=NotificationLevel.NORMAL))

#       TODO Necesita cambiarse, para que cuando el socket está desconectado
        for k, v in self.queues.items():
            v.join()

    def is_open(self):
        return self._dev_connection and self._dev_connection.isOpen()

    def write(self, data):
        self.queues['write_data'].put_nowait(data + "\r")

    def send_notification(self, notification: NoticeBase):
        logger.info(notification.message)
