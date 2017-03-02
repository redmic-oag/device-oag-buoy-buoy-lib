# -*- coding: utf-8 -*-

import logging
import time
from queue import Queue
from threading import Thread

import psycopg2
import serial
from psycopg2 import DatabaseError, IntegrityError, errorcodes
from psycopg2.extensions import AsIs
from psycopg2.extras import DictCursor, DictRow

from typing import List, AnyStr
from buoy.lib.protocol.item import BaseItem

logger = logging.getLogger(__name__)


class DeviceReader(Thread):
    """ Clase encargada de leer y parsear los datos que devuelve el dispositivo """
    def __init__(self):
        Thread.__init__(self)
        self.queue_save_data = None
        self.device = None

    def set_paramaters(self, **kwargs):
        # TODO chequear que los parámetros esten rellenos
        self.queue_save_data = kwargs.pop('queue_save_data')
        self.device = kwargs.pop('device')

    def run(self):
        buffer = ''
        while self.device.isOpen:
            try:
                buffer += self.device.read(self.device.inWaiting()).decode()
                if '\n' in buffer:
                    lines = buffer.split('\n')
                    last_received = lines[-2]
                    buffer = lines[-1]

                    item = self.parser(last_received)
                    if item:
                        self.queue_save_data.put_nowait(item)

                    logger.info(last_received)
            except (OSError, Exception):
                logger.info("Lost your connection to the device")
                break

    def parser(self, data):
        pass


class DeviceWriter(Thread):
    """ Clase encargada de enviar datas al dispositivo """
    def __init__(self):
        Thread.__init__(self)

        self.queue_write_data = None
        self.device = None

    def set_paramaters(self, **kwargs):
        # TODO chequear que los parámetros esten rellenos
        self.queue_write_data = kwargs.pop('queue')
        self.device = kwargs.pop('device')

    def run(self):
        while self.device.isOpen:
            data = self.queue_write_data.get()
            self.device.write(data.encode())
            time.sleep(1)


class DeviceSave(Thread):
    def __init__(self, **kwargs):
        Thread.__init__(self)
        self.queue_save_data = None

        self.db = DeviceDB(**kwargs)

    def set_paramaters(self, **kwargs):
        # TODO chequear que los parámetros esten rellenos
        self.queue_save_data = kwargs.pop('queue_save_data')

    def run(self):
        while True:
            item = self.queue_save_data.get()
            self.save(item)

    def save(self, item):
        """ Guarda en la base de datos """
        self.db.save([item])


class DeviceDB(object):
    """ Clase encargada de gestionar la base de datos """
    def __init__(self, **kwargs):

        self.connection = None
        self.cursor = None
        self.num_attempts = 3

        self.connect(kwargs.pop("db_config"))
        self.tablename_data = kwargs.get("db_tablename")

        self._insert_sql = """INSERT INTO """ + self.tablename_data + """(%s) VALUES %s"""
        self._find_by_id_sql = """SELECT * FROM """ + self.tablename_data + """ WHERE id = %s"""
        self._update_status_sql = """UPDATE """ + self.tablename_data + """ SET sended=%s WHERE id = ANY(%s)"""
        self._select_items_to_send_sql = """SELECT * FROM """ + self.tablename_data + \
                                         """ WHERE sended IS false AND num_attempts < """ + str(self.num_attempts) + \
                                         """ ORDER BY datetime LIMIT %s OFFSET %s"""

    def connect(self, db_config):
        logger.debug("Connecting to database")
        self.connection = psycopg2.connect(**db_config)
        self.cursor = self.connection.cursor(cursor_factory=psycopg2.extras.DictCursor)

    def save(self, items: List):
        """ Inserta un nuevo registro en la base de datos """
        result = {
            'ok': [],
            'fail': []
        }

        for item in items:
            try:
                sql = self.__create_insert_sql(item)
                self.cursor.execute(sql)
                self.connection.commit()
                result['ok'].append(item.id)
            except IntegrityError as e:
                if e.pgcode == errorcodes.UNIQUE_VIOLATION:
                    result['ok'].append(item.id)
                    logger.warning("Inserting data already inserted")
                else:
                    result['fail'].append(item.id)
                    logger.exception("No insert data")
            except DatabaseError:
                result['fail'].append(item.id)
                logger.exception("No insert data")

        return result

    def get(self, identifier):
        """ Retorna un registro un registro dado un identificador """
        sql = self.cursor.mogrify(self._find_by_id_sql, (identifier,))
        self.execute(sql)
        row = self.cursor.fetchone()

        return row

    def get_items_to_send(self, cls, size: int=100, offset: int=0) -> List[DictRow]:
        """ Retorna la lista de registros nuevos a enviar """
        sql = self.cursor.mogrify(self._select_items_to_send_sql, (size, offset))
        self.execute(sql)
        rows = self.cursor.fetchall()
        items = []
        for row in rows:
            items.append(cls(**row))
        return items

    def update_status(self, ids: List[int], status=True):
        if len(ids):
            sql = self.cursor.mogrify(self._update_status_sql, (status, ids))
            self.execute(sql)
            self.connection.commit()

    def __create_insert_sql(self, item):
        columns = self.__get_column_names(item)
        values = [getattr(item, column) for column in columns]
        sql = self.cursor.mogrify(self._insert_sql, (AsIs(','.join(columns)), tuple(values)))

        return sql

    @staticmethod
    def __get_column_names(item: BaseItem) -> List[AnyStr]:
        """ Retorna una lista con el nombre de las columnas
        :param item: BaseItem
        :return: list
        """
        columns = list(dict(item).keys())
        columns.remove('id')

        return columns

    def execute(self, sql):
        logger.debug("Execute sql %s", sql)

        return self.cursor.execute(sql)


class Device(object):
    def __init__(self, device_name: None, **kwargs):
        self.serial_config = kwargs.pop('serial_config', None)
        db_config = kwargs.pop('db_config')

        # Device
        self.name = device_name
        self._dev_connection = None

        self._queue_write_data = Queue()
        self._queue_save_data = Queue()

        # Hilos
        self._thread_reader = DeviceReader()
        self._thread_writer = DeviceWriter()
        self._thread_save = DeviceSave(db_tablename=self.name, db_config=db_config)

    def connect(self):
        logger.info("Connecting to device")
        try:
            self._dev_connection = serial.Serial(**self.serial_config)
        except:
            return None

        if self._dev_connection:
            logger.info("Connected to device")

            self._thread_reader.set_paramaters(device=self._dev_connection, queue_save_data=self._queue_save_data)
            self._thread_writer.set_paramaters(device=self._dev_connection, queue=self._queue_write_data)
            self._thread_save.set_paramaters(queue_save_data=self._queue_save_data)

            self._thread_reader.start()
            self._thread_writer.start()
            self._thread_save.start()

    def disconnect(self):
        if self.is_open():
            self._dev_connection.close()
            logger.info("Disconnected to device")

    def is_open(self):
        return self._dev_connection and self._dev_connection.isOpen()

    def write(self, data):
        self._queue_write_data.put_nowait(data + "\r")
