# -*- coding: utf-8 -*-

import logging
import json

from typing import List

from threading import Thread
from socketIO_client import BaseNamespace

from buoy.lib.device.database import DeviceDB, BaseItem
from buoy.lib.notification.common import NoticeBase, NoticeType
from buoy.lib.notification.client.common import DataEncoder, NoticeQueue, NotificationThread

logger = logging.getLogger(__name__)


class WaitDataThread(Thread):
    def __init__(self, queue_data: NoticeQueue, db: DeviceDB, cls, emit):
        Thread.__init__(self)
        self.db = db
        self.cls = cls
        self.queue_data = queue_data
        self._emit = emit

    def run(self):
        """
        Envía los datos al servidor de notificaciones
        :return:
        """
        items = self.waiting_data()
        json_to_send = json.dumps(items, sort_keys=True, cls=DataEncoder)

        self.emit("new_data", json_to_send)

    def waiting_data(self) -> List[BaseItem]:
        """
        Espera por los datos, si existen datos en la base de datos tienen preferencia
        a las que envía el dispositivo

        :return Retorna una lista de datos
        :rtype Lista de tipo BaseItem
        """
        items = self.db.get_items_to_send(self.cls)
        if not len(items):
            notice = self.queue_data.get()
            items = [notice.data]

        return items

    def emit(self, event: str, data):
        self._emit(event, data)


class DataDeviceNamespaceClient(BaseNamespace):
    """
        Clase encargada de conectarse son el servidor de notificaciones
        al cual, le van a enviar los datos
    """
    def __init__(self, io, path):
        super(DataDeviceNamespaceClient, self).__init__(io, path)
        self.queue_data = io.queue_notice.queue_type(NoticeType.DATA)
        self.db = io.db
        self.cls = io.cls
        self._sender_up = False
        self._sender_busy = False
        self.device_id = "PB200"
        self.thread_wait_data = None

    @property
    def sender_busy(self):
        return self._sender_busy

    @sender_busy.setter
    def sender_busy(self, value: bool):
        """
        Actualiza el estado del servicio, en caso de que se halla una petición en curso se pone en estado 'busy',
        para evitar el colapso del servicio de envío de datos al servidor, y se cambia de estado cuando se recibe
        la respuesta de que los datos se han enviado

        :param value: Estado del servicio
        :return:
        """
        self._sender_busy = value
        if not value and self.sender_up:
            self.send_data()

    @property
    def sender_up(self):
        return self._sender_up

    @sender_up.setter
    def sender_up(self, value: bool):
        """
        Actualiza el estado del servicio del envío de datos al servidor, en caso de que esté activo
        entonces se puede empezar a enviar datos, en caso contrario se cancela el envío.

        :param value: Estado del servicio de envío de datos al servidor
        :return:
        """
        self._sender_up = value
        if value and not self.sender_busy:
            self.send_data()
        elif not value:
            self.sender_busy = False

    def on_connect(self):
        self.emit("add_device", self.device_id)

    def on_reconnect(self):
        self.emit("add_device", self.device_id)

    def on_disconnect(self):
        """
        Emite el evento de 'rm_device' para que el servidor
        de notificaciones lo elimine de la lista de dispositivos
        """
        self.emit("rm_device", self.device_id)

    def on_sender_status(self, args):
        """ Evento que se recibe cuando el servicio de envío de datos cambia de estado """
        status = False
        if args == "true":
            status = True

        self.sender_up = status

    def on_sended_data(self, args):
        """ Marca los items como enviados correctamente, o incrementa el número de intentos en el caso de error """
        items = json.loads(args)

        self.update_status(items['items_ok'])
        self.update_status(items['items_fail'], False)
        self.sender_busy = False

    def update_status(self, items: List, status: bool = True):
        """
        Actualiza el estado de los items que han sido enviados y de los cuales se ha recibido la notificación
        desde el servidor

        :param items: Lista de datos
        :param status: Estado del item, True (Correcto) y False (Fallido). Por defecto True
        :return:
        """
        if items and len(items):
            ids = []
            for item in items:
                ids.append(item['id'])
            self.db.update_status(ids, status)

    def send_data(self):
        self.sender_busy = True
        self.thread_wait_data = WaitDataThread(db=self.db, queue_data=self.queue_data, cls=self.cls, emit=self.emit)
        self.thread_wait_data.start()


class NoticeDeviceThread(NotificationThread):
    def __init__(self, queue_notice: NoticeQueue, db: DeviceDB, cls: BaseItem, **kwargs):
        super(NoticeDeviceThread, self).__init__(queue_notice=queue_notice)
        self.db = db
        self.cls = cls
        self.data_namespace = None

    def prepare_sockect(self):
        super().prepare_sockect()
        self.socket.db = self.db
        self.socket.cls = self.cls
        self.data_namespace = self.socket.define(DataDeviceNamespaceClient, '/data')


class NotificationClient(object):
    def __init__(self):
        self.queues = {'notice': NoticeQueue()}

        self._notification_thread = NotificationThread(queue_notice=self.queues['notice'])
        self._notification_thread.start()

    def send_notification(self, notification: NoticeBase):
        logger.info(str(notification))
        notification.daemon = self.daemon_name if hasattr(self, 'daemon_name') else __file__

        self.queues['notice'].put_nowait(notification)


class NoticeDeviceClient(object):
    def __init__(self, db, cls):
        self.queues = {'notice': NoticeQueue()}

        self._notification_thread = NoticeDeviceThread(queue_notice=self.queues['notice'], db=db, cls=cls)
        self._notification_thread.start()

    def send_notification(self, notification: NoticeBase):
        logger.info(str(notification))
        notification.daemon = self.daemon_name if hasattr(self, 'daemon_name') else __file__

        self.queues['notice'].put_nowait(notification)
