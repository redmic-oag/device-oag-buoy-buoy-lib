# -*- coding: utf-8 -*-

import logging
from copy import copy
from queue import Queue, Full
from typing import List

from serial import Serial

from buoy.base.data.item import ItemQueue, BaseItem
from buoy.base.device.exceptions import LostConnectionException, ProcessDataExecption
from buoy.base.device.threads.base import DeviceBaseThread

logger = logging.getLogger(__name__)


class DeviceReader(DeviceBaseThread):
    """ Clase encargada de leer y parsear los datos que devuelve el dispositivo """

    def __init__(self, device: Serial, queue_notice: Queue, **kwargs):
        self.char_splitter = kwargs.pop('char_splitter', '\n')
        super(DeviceReader, self).__init__(device, queue_notice)
        self.buffer = ''

        self.queue_save_data = kwargs.pop('queue_save_data', None)
        if not self.queue_save_data:
            logging.info("No save data in database")
        self.queue_send_data = kwargs.pop('queue_send_data', None)
        if not self.queue_send_data:
            logging.info("No send data in real-time")

    def activity(self):
        try:
            self.read_data()
            logger.debug("Waiting data")
            if not self.is_buffer_empty():
                self.process_data()

        except (OSError, Exception) as ex:
            logger.error("Device disconnected")
            self.error(LostConnectionException(exception=ex))

    def read_data(self):
        logger.debug("Data in buffer %s" % self.buffer)
        self.buffer += self.device.read(self.device.in_waiting).decode()

    def is_buffer_empty(self):
        return self.char_splitter not in self.buffer

    def process_data(self):
        logger.debug("Proccessing data: %s", self.buffer)
        buffer = self.buffer.rsplit(self.char_splitter, 1)
        try:
            self.buffer = buffer[1].strip()
        except IndexError as ex:
            raise ProcessDataExecption(message="Proccesing data without char split", exception=ex)
        for line in self.split_by_lines(buffer[0]):
            item = self.parser(line)
            if item:
                self.put_in_queues(item)
            logger.debug("Received data - " + line)

    def split_by_lines(self, buffer: str) -> List[str]:
        lines = buffer.split(self.char_splitter)
        return [l.strip() for l in lines if len(l.strip())]

    def parser(self, data) -> BaseItem:
        pass

    def put_in_queues(self, item: BaseItem):
        logger.debug("Item readed from device - %s" % str(item))

        if self.queue_save_data and not self.queue_save_data.full():
            try:
                self.queue_save_data.put_nowait(ItemQueue(data=copy(item)))
            except Full:
                logger.error("Save data queue is full")

        if self.queue_send_data and not self.queue_send_data.full():
            try:
                self.queue_send_data.put_nowait(item)
            except Full:
                logger.warning("Send data queue is full")
