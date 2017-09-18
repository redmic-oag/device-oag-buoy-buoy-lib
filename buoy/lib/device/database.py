# -*- coding: utf-8 -*-

import logging
import psycopg2

from psycopg2 import DatabaseError, IntegrityError, errorcodes
from psycopg2.extensions import AsIs
from psycopg2.extras import DictCursor, DictRow

from typing import List, AnyStr
from buoy.lib.protocol.item import BaseItem

logger = logging.getLogger(__name__)


class DeviceDB(object):
    """ Clase encargada de gestionar la base de datos """
    def __init__(self, db_config, db_tablename):

        self.connection = None
        self.num_attempts = 3

        self.connect(db_config)
        self.tablename_data = db_tablename

        self._insert_sql = """INSERT INTO """ + self.tablename_data + """(%s) VALUES %s RETURNING id"""
        self._find_by_id_sql = """SELECT * FROM """ + self.tablename_data + """ WHERE id = %s"""
        self._update_status_sql = """UPDATE """ + self.tablename_data + """ SET sended=%s WHERE id = ANY(%s)"""
        self._select_items_to_send_sql = """SELECT * FROM """ + self.tablename_data + \
                                         """ WHERE sended IS false AND num_attempts < """ + str(self.num_attempts) + \
                                         """ ORDER BY datetime LIMIT %s OFFSET %s"""

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
                logger.warning("Inserting data already inserted")
            else:
                logger.exception("No insert data")
        except DatabaseError as e:
            logger.exception("No insert data")

        return item

    def get(self, identifier):
        """ Retorna un registro un registro dado un identificador """
        with self.get_cursor() as cur:
            sql = cur.mogrify(self._find_by_id_sql, (identifier,))
            cur.execute(sql)
            row = cur.fetchone()

        return row

    def __get_items_to_send(self, cls, *args):
        """ Retorna la lista de registros nuevos a enviar """
        with self.get_cursor() as cur:
            sql = cur.mogrify(self._select_items_to_send_sql, *args)
            cur.execute(sql)
            rows = cur.fetchall()

        items = []
        for row in rows:
            items.append(cls(**row))
        return items

    def get_items_to_send(self, cls, size: int=100, offset: int=0) -> List[DictRow]:
        return self.__get_items_to_send(cls, (size, offset, ))

    def update_status(self, ids: List[int], status=True):
        if len(ids):
            with self.get_cursor() as cur:
                sql = cur.mogrify(self._update_status_sql, (status, ids))
                cur.execute(sql)
            self.connection.commit()

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
        columns.remove('id')

        return columns
