# -*- coding: utf-8 -*-

import logging
import json

from datetime import time

from flask import Flask
from flask_socketio import SocketIO
from flask_socketio import Namespace, emit
from queue import Empty

from psycopg2.extras import DictRow
from threading import Thread

from typing import List
from buoy.lib.protocol.item import DataEncoder
from buoy.lib.device.base import DeviceDB
from buoy.lib.notification.common import NotificationLevel, Notification, BaseItem
from buoy.lib.notification.client.common import NoticeQueue

logger = logging.getLogger(__name__)


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
        return super(NotificationDB, self).__get_items_to_send(cls, (size, offset, level, ))


class NotificationTargetThread(Thread):
    def __init__(self, queue_data: NoticeQueue, db: DeviceDB, cls, emit):
        Thread.__init__(self)
        self.db = db
        self.cls = cls
        self.queue_data = queue_data
        self._emit = emit
        self._timeout_wait_notice = 5

    def run(self):
        """
        Envía los datos al servidor de notificaciones
        :return:
        """
        items = self.waiting_data()
        json_to_send = json.dumps(items, sort_keys=True, cls=DataEncoder)

        self.emit("send_notification", json_to_send)

    def waiting_data(self) -> List[BaseItem]:
        """
        Espera por los datos, si existen datos en la base de datos tienen preferencia
        a las que envía el dispositivo

        :return Retorna una lista de datos
        :rtype Lista de tipo BaseItem
        """
        items = None
        while not items or not len(items):
            try:
                notice = self.queue_data.get(timeout=self._timeout_wait_notice)
                items = [notice.data]
            except Empty:
                items = self.db.get_items_to_send(self.cls)

        return items

    def emit(self, event: str, data):
        self._emit(event, data)


class NotificationNamespace(Namespace):
    def __init__(self, namespace, **kwargs):
        Namespace.__init__(self, namespace=namespace)
        db_config = kwargs.pop('db_config')
        self.db = NotificationDB(db_config=db_config, db_tablename="notification")
        self.sources = {}
        self.targets = {}

    def on_connect(self):
        pass

    def on_disconnect(self):
        pass

    def on_join_sources(self, data):
        self.sources[data] = True

    def on_join_targets(self, id):
        self.targets[id] = True

    def on_new_notification(self, data):
        """
        Recibe las notificaciones de los clientes, la guarda en la base de datos
        y la envía al servicio de envío de notificaciones
        :param data:
        :return:
        """
        notification = self.json_to_notification(data)
        notification = self.db.save(notification)

        # TODO si existe target entonces añade los datos a una colo que estará escuchando el hilo

        emit("send_notification", notification.to_json())

    def on_sended_notification(self, data):
        """
        Envía la confirmación del envío de las notificaciones
        """
        notification = self.json_to_notification(data)
        self.db.update_status([notification.id])

    @staticmethod
    def json_to_notification(data):
        a = json.loads(data)
        return Notification(**a)


class DataNamespace(Namespace):
    def __init__(self, namespace, **kwargs):
        Namespace.__init__(self, namespace=namespace)
        self.clients = []

    def on_connect(self):
        pass

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

    def on_add_device(self, data):
        emit("sender_status", "true")

#    def on_sended_data(self, items_ok, items_error):
#        self.emit("sended_data", items_ok, items_error)


class NotificationThread(Thread):
    def __init__(self, db_config, **kwargs):
        super().__init__(**kwargs)
        self.app = Flask(__name__)
        self.app.debug = False
        self.socketio = SocketIO(self.app)

        self.socketio.on_namespace(NotificationNamespace('/notifications', db_config=db_config))
        self.socketio.on_namespace(DataNamespace('/data'))

    def run(self):
        self.socketio.run(self.app)


class NotificationServer(object):
    def __init__(self):
        self._notification_thread = NotificationThread()
        self._notification_thread.start()


if __name__ == "__main__":
    NotificationServer()
