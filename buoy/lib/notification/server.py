# -*- coding: utf-8 -*-

import logging
import json
import string
import random


from datetime import time

from flask import Flask
from flask_socketio import SocketIO
from flask_socketio import Namespace, emit, send

from psycopg2.extras import DictRow
from psycopg2 import DatabaseError
from threading import Thread

from typing import List
from buoy.lib.protocol.item import DataEncoder
from buoy.lib.device.base import DeviceDB
from buoy.lib.notification.common import NoticeData, NotificationLevel
from buoy.lib.notification.common import Notification as NotificationItem

#logger = logging.getLogger(__name__)
logger = logging.basicConfig(filename='example.log', level=logging.DEBUG)


class NotificationDB(DeviceDB):
    """ Clase encargada de gestionar la base de datos """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.num_attempts = 1
        self._select_items_to_send_sql = """SELECT * FROM """ + self.tablename_data + \
                                         """ WHERE sended IS false """ + \
                                         """ ORDER BY datetime LIMIT %s OFFSET %s"""

    def get_items_to_send(self, cls, size: int=100, offset: int=0, level: NotificationLevel=NotificationLevel.LOW) \
            -> List[DictRow]:
        """ Retorna la lista de registros nuevos a enviar """

        sql = self.cursor.mogrify(self._select_items_to_send_sql, (size, offset, level))
        self.execute(sql)
        rows = self.cursor.fetchall()
        items = []
        for row in rows:
            items.append(cls(**row))
        return items

    def save(self, items: List):
        """ Inserta un nuevo registro en la base de datos """
        for item in items:
            try:
                sql = self.create_insert_sql(item)
                self.cursor.execute(sql)
            except DatabaseError as e:
                logger.exception("No insert data")
            self.connection.commit()


class NotificationNamespace(Namespace):
    def __init__(self, namespace, **kwargs):
        Namespace.__init__(self, namespace=namespace)
        db_config = kwargs.pop('db_config')
        self.db = NotificationDB(db_config=db_config, db_tablename="notification")

    def on_connect(self):
        """ Cuando se conecta un cliente pide las notificaciones pendientes """
        logger.info("Connected")
        emit("get_notifications")

    def on_disconnect(self):
        pass

    def on_get_notifications(self, data):
        notificacions = self.db.get_items_to_send()
        for notification in notificacions:
            json_to_send = json.dumps(notification, sort_keys=True, cls=DataEncoder)
            emit("new_notification", json_to_send)

    def on_new_notification(self, data):
        """ Recibe las notificaciones de los clientes """
        logger.info("New Notification")

        notification = self.json_to_notification(data)
        self.db.save([notification])
        json_to_send = json.dumps(notification, sort_keys=True, cls=DataEncoder)

        emit("notification_received")
        emit("new_notification", json_to_send, broadcast=True)

    def on_sended_notification(self, data):
        """ Envía la confirmación del envío de las notificaciones """
        notification = self.json_to_notification(data)
        self.db.update_status([notification.id])

    @staticmethod
    def json_to_notification(data):
        a = json.loads(data)
        return NotificationItem(**a)


class DataNamespace(Namespace):
    def __init__(self, namespace, **kwargs):
        Namespace.__init__(self, namespace=namespace)
        self.clients = []

    def on_connect(self):
        """ Cuando se conecta un dispositivo """
#        logger.info("Connected - Emit 'sended_data'")


    def on_disconnect(self):
        pass

    def on_new_data(self, data):
        items = json.loads(data)
        response = {
            'items_ok': items,
            'items_fail': None
        }

        json_to_send = json.dumps(response, sort_keys=True, cls=DataEncoder)

#        emit("new_data", json_to_send, broadcast=True)
        emit("sended_data", json_to_send)

    def on_add_device(self, device_id):
        self.clients.append(device_id)
        emit("sender_status", True)

#    def on_sended_data(self, items_ok, items_error):
#        self.emit("sended_data", items_ok, items_error)


class NotificationThread(Thread):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.app = Flask(__name__)
        self.app.debug = False
        self.socketio = SocketIO(self.app)
        db_config = {
            'database': 'boyadb',
            'user': 'boya',
            'password': 'b0y4_04G',
            'host': '127.0.0.1'
        }
        #self.socketio.on_namespace(NotificationNamespace('/notifications', db_config=db_config))
        self.socketio.on_namespace(DataNamespace('/data'))

    def run(self):
        self.socketio.run(self.app)


class Notification(object):
    def __init__(self):
        self._notification_thread = NotificationThread()
        self._notification_thread.start()


if __name__ == "__main__":
    Notification()
