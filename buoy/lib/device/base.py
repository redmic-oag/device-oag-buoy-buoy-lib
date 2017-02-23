# -*- coding: utf-8 -*-

import configparser
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
from buoy.lib.utils.config import Config
from buoy.lib.protocol.item import BaseItem

logger = logging.getLogger(__name__)


class DeviceConf(object):
    """ Clase para definir la conexión del dispositivo """
    def __init__(self, **kwargs):
        self._filename = Config().filename()
        self._device = kwargs.pop('device')
        self.SECTION = 'Device - %s' % self._device

        self._read_config()

    def _read_config(self):
        config = configparser.ConfigParser()
        config.read(self._filename)

        self._port = config.get(self.SECTION, 'port')
        self._baudrate = config.getint(self.SECTION, 'baud_rate')
        self._timeout = config.getint(self.SECTION, 'timeout')
        self._stop_bits = config.getint(self.SECTION, 'stop_bits')
        self._parity = config.get(self.SECTION, 'parity')
        self._byte_size = config.getint(self.SECTION, 'byte_size')

    def __iter__(self):
        yield 'device', getattr(self, 'device')
        yield 'port', getattr(self, 'port')
        yield 'baudrate', getattr(self, 'baudrate')
        yield 'parity', getattr(self, 'parity')
        yield 'stopbits', getattr(self, 'stopbits')
        yield 'bytesize', getattr(self, 'bytesize')
        yield 'timeout', getattr(self, 'timeout')

    @property
    def device(self):
        return self._device

    @property
    def port(self):
        return self._port

    @property
    def baudrate(self):
        return self._baudrate

    @property
    def parity(self):
        return self._parity

    @property
    def stopbits(self):
        return self._stop_bits

    @property
    def bytesize(self):
        return self._byte_size

    @property
    def timeout(self):
        return self._timeout

    def __str__(self):
        return ("DEVICE: {device}\n"
                "Port: {port}\n"
                "Baudrate: {baudrate}\n"
                "Parity: {parity}\n"
                "Stop bits: {stopbits}\n"
                "Byte size: {bytesize}\n"
                "TimeOut: {timeout}").format(**dict(self))


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
            buffer += self.device.read(self.device.inWaiting()).decode()
            if '\n' in buffer:
                lines = buffer.split('\n')
                last_received = lines[-2]
                buffer = lines[-1]

                item = self.parser(last_received)
                if item:
                    self.queue_save_data.put_nowait(item)

                # TODO Cambiar por un log
                logger.info(last_received)

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

        connection = kwargs.pop("connection_db")
        tablename_data = kwargs.pop("tablename_data")

        self.db = DeviceDB(connection_db=connection, tablename_data=tablename_data)

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
        self.connection = kwargs.get("connection_db")
        self.cursor = self.connection.cursor(cursor_factory=psycopg2.extras.DictCursor)
        self.num_attempts = 3

        self.tablename_data = kwargs.get("tablename_data")
        self._insert_sql = """INSERT INTO """ + self.tablename_data + """(%s) VALUES %s"""
        self._find_by_id_sql = """SELECT * FROM """ + self.tablename_data + """ WHERE id = %s"""
        self._update_status_sql = """UPDATE """ + self.tablename_data + """ SET sended=%s WHERE id = ANY(%s)"""
        self._select_items_to_send_sql = """SELECT * FROM """ + self.tablename_data + \
                                         """ WHERE sended IS false AND num_attempts < """ + str(self.num_attempts) + \
                                         """ ORDER BY datetime LIMIT %s OFFSET %s"""

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
                    logger.exception("No insert data", exc_info=True)
            except DatabaseError:
                result['fail'].append(item.id)
                logger.exception("No insert data", exec_info=True)

        return result

    def get(self, identifier):
        """ Retorna un registro un registro dado un identificador """
        sql = self.cursor.mogrify(self._find_by_id_sql, (identifier,))
        self.execute(sql)
        row = self.cursor.fetchone()

        return row

    def get_items_to_send(self, size: int=100, offset: int=0) -> List[DictRow]:
        """ Retorna la lista de registros nuevos a enviar """
        sql = self.cursor.mogrify(self._select_items_to_send_sql, (size, offset))
        self.execute(sql)
        rows = self.cursor.fetchall()

        return rows

    def update_status(self, ids: List[int], status=True):
        sql = self.cursor.mogrify(self._update_status_sql, (status, ids))
        self.execute(sql)

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
        # DB
        self.dbname = "boyadb"
        self.username = "boya"
        self.password = "b0y4_04G"
        self.__connect_db()

        # Device
        self._dev_name = device_name
        self._dev_connection = None
        self._device_conf = DeviceConf(device=self._dev_name)

        self._queue_write_data = Queue()
        self._queue_save_data = Queue()

        # Hilos
        self._thread_reader = DeviceReader()
        self._thread_writer = DeviceWriter()
        self._thread_save = DeviceSave(tablename_data=self._dev_name, connection_db=self.db)

    def __connect_db(self):
        logger.debug("Connecting to database")
        self.db = psycopg2.connect(database=self.dbname, user=self.username, password=self.password, host="127.0.0.1")

    def connect(self):
        logger.info("Connecting to device")
        try:
            dev_conf = dict(self._device_conf)
            dev_conf.pop("device")
            self._dev_connection = serial.Serial(**dev_conf)
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
