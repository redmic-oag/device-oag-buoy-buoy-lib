# -*- coding: utf-8 -*-

import logging
from typing import List, AnyStr

import psycopg2
from psycopg2 import DatabaseError, IntegrityError, errorcodes
from psycopg2.extensions import AsIs
from psycopg2.extras import DictCursor, DictRow, register_uuid

from buoy.base.data.item import BaseItem

register_uuid()
logger = logging.getLogger(__name__)


class DeviceDB(object):
    """ Clase encargada de gestionar la base de datos """

    def __init__(self, db_config, db_tablename, cls_item, **kwargs):

        self.connection = None
        self.connect(db_config)
        self.tablename_data = db_tablename
        self.cls = cls_item
        self.window_time = kwargs.pop('window_time', 300)

        self._insert_sql = """INSERT INTO """ + self.tablename_data + """(%s) VALUES %s RETURNING uuid"""
        self._find_by_id_sql = """SELECT * FROM """ + self.tablename_data + """ WHERE uuid = ANY(%s)"""
        self._update_status_sql = """UPDATE """ + self.tablename_data + """ SET sent=%s WHERE uuid = ANY(%s)"""
        self._select_items_to_send_sql = """SELECT * FROM """ + self.tablename_data + \
                                         """ WHERE sent IS false AND num_attempts < %s """ + \
                                         """AND date < now() - %s * interval '1 second' """ + \
                                         """ORDER BY date LIMIT %s"""

    def connect(self, db_config):
        logger.debug("Connecting to database")
        self.connection = psycopg2.connect(**db_config)

    def save(self, item: BaseItem) -> BaseItem:
        """ Inserta un nuevo registro en la base de datos """
        try:
            with self.get_cursor() as cur:
                sql = self.create_insert_sql(item, cur)
                cur.execute(sql)
                item.id = cur.fetchone()[0]
            self.connection.commit()
        except IntegrityError as e:
            if e.pgcode == errorcodes.UNIQUE_VIOLATION:
                logger.warning("The data exists in database yet")
            else:
                logger.exception("No insert data", exc_info=e)
        except DatabaseError as e:
            logger.exception("No insert data", exc_info=e)

        return item

    def get(self, identifier):
        """ Retorna un registro un registro dado un identificador """
        with self.get_cursor() as cur:
            sql = cur.mogrify(self._find_by_id_sql, (identifier,))
            cur.execute(sql)
            row = cur.fetchone()

        return row

    def _get_items_to_send(self, *args):
        """ Retorna la lista de registros nuevos a enviar """
        with self.get_cursor() as cur:
            sql = cur.mogrify(self._select_items_to_send_sql, *args)
            cur.execute(sql)
            rows = cur.fetchall()

        items = []
        for row in rows:
            items.append(self.cls(**row))

        return items

    def get_items_to_send(self, **kwargs) -> List[DictRow]:

        window_time = kwargs.pop('window_time', 900)
        max_attemps = kwargs.pop('max_attemps', 3)
        size = kwargs.pop('size', 100)

        return self._get_items_to_send((max_attemps, window_time, size))

    def update_status(self, uuids: List, status=True):
        if len(uuids):
            try:
                with self.get_cursor() as cur:
                    sql = cur.mogrify(self._update_status_sql, (status, uuids))
                    cur.execute(sql)
                self.connection.commit()
            except DatabaseError:
                logger.exception("No update data")

    def set_sent(self, uuid):
        self.update_status([uuid], status=True)

    def set_failed(self, uuid):
        self.update_status([uuid], status=False)

    def create_insert_sql(self, item, cursor):
        columns = self.__get_column_names(item)
        values = [getattr(item, column) for column in columns]
        sql = cursor.mogrify(self._insert_sql, (AsIs(','.join(columns)), tuple(values)))

        return sql

    def get_cursor(self):
        return self.connection.cursor(cursor_factory=psycopg2.extras.DictCursor)

    @staticmethod
    def __get_column_names(item: BaseItem) -> List[AnyStr]:
        """ Retorna una lista con el nombre de las columnas
        :param item: BaseItem
        :return: list
        """
        columns = list(dict(item).keys())

        return columns
