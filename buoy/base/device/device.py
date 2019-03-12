# -*- coding: utf-8 -*-

import logging
from queue import Queue, Empty

from serial import Serial, SerialException

from buoy.base.device.threads.mqtt import MqttThread
from buoy.base.device.threads.resender import DBToSendThread
from buoy.base.device.threads.save import SaveThread
from buoy.base.device.exceptions import DeviceNoDetectedException

logger = logging.getLogger(__name__)


class Device(object):
    def __init__(self, *args, **kwargs):
        self.serial_config = kwargs.pop('serial_config', None)
        self.db = kwargs.pop('db')

        self.cls_reader = kwargs.pop('cls_reader', None)
        self.cls_writer = kwargs.pop('cls_writer', None)
        self.cls_save = kwargs.pop('cls_save', SaveThread)
        self.cls_send = kwargs.pop('cls_send', MqttThread)
        self.cls_reader_from_db = kwargs.pop('cls_reader_from_db', DBToSendThread)
        self.mqtt = kwargs.pop('mqtt', None)

        self.qsize_send_data = kwargs.pop('qsize_send_data', 1000)

        self.queues = {}
        self._create_queues()

        # Device
        self.name = kwargs.pop('device_name')
        self._dev_connection = None

    def _create_queues(self):
        for queue_name in ['notice', 'write_data', 'save_data', 'send_data']:
            qsize = 0
            if queue_name == 'send_data':
                qsize = self.qsize_send_data
            self.queues[queue_name] = Queue(maxsize=qsize)

    def run(self):
        try:
            self.connect()
            self._create_threads()
            self._start_threads()
            self.configure()
            self._listener_exceptions()
        except Exception as ex:
            logger.error(ex)
            raise ex

    def connect(self):
        logger.info("Connecting to device")
        try:
            self._dev_connection = Serial(**self.serial_config)
        except SerialException as ex:
            raise DeviceNoDetectedException(process=self.name, exception=ex)
        logger.info("Connected to device")

    def _create_threads(self):
        if self.cls_writer:
            self._thread_writer = self.cls_writer(device=self._dev_connection,
                                                  queue_write_data=self.queues['write_data'],
                                                  queue_notice=self.queues['notice'])
        if self.cls_reader:
            self._thread_reader = self.cls_reader(device=self._dev_connection,
                                                  queue_save_data=self.queues['save_data'],
                                                  queue_send_data=self.queues['send_data'],
                                                  queue_notice=self.queues['notice'])
        if self.cls_save:
            self._thread_save = self.cls_save(queue_save_data=self.queues['save_data'],
                                              queue_notice=self.queues['notice'],
                                              db=self.db)
        if self.cls_reader_from_db:
            self._thread_send = self.cls_reader_from_db(queue_send_data=self.queues['send_data'],
                                                        queue_notice=self.queues['notice'],
                                                        db=self.db)
        if self.cls_send:
            self._thread_send = self.cls_send(queue_send_data=self.queues['send_data'],
                                              queue_data_sent=self.queues['save_data'],
                                              queue_notice=self.queues['notice'],
                                              **self.mqtt)

    def _start_threads(self):
        self._run_action_threads(action='start')

    def _run_action_threads(self, action='start'):
        prefix = '_thread_'
        names = ['reader', 'writer', 'save', 'send', 'reader_from_db']

        for name in names:
            field = prefix + name
            if hasattr(self, field):
                thread = getattr(self, field)
                getattr(thread, action)()

    def configure(self):
        pass

    def _listener_exceptions(self):
        while self.is_open():
            try:
                ex = self.queues['notice'].get(timeout=0.2)
                raise ex
            except Empty:
                pass

    def disconnect(self):
        logger.info("Disconnecting to device")
        self._stop_threads()
        if self.is_open():
            self._dev_connection.close()
        logger.info("Disconnected to device")

    def _stop_threads(self):
        self._run_action_threads(action='stop')

    def is_open(self):
        return self._dev_connection and self._dev_connection.is_open and self.is_active()

    def write(self, data):
        self.queues['write_data'].put_nowait(data + "\r")
