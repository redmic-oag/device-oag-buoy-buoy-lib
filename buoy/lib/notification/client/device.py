# -*- coding: utf-8 -*-

import logging
import json

from typing import List

from threading import Thread
from queue import PriorityQueue, Queue
from socketIO_client import SocketIO, BaseNamespace

from buoy.lib.device.database import DeviceDB
from buoy.lib.notification.common import NoticeBase, NotificationLevel, NoticeType
from buoy.lib.notification.common import Notification
from buoy.lib.sender.sender import Sender
from buoy.lib.protocol.item import DataEncoder, BaseItem

logger = logging.getLogger(__name__)


class NoticePriorityQueue(PriorityQueue):
    def __init__(self, notice_type: NoticeType):
        super().__init__()
        self.type = notice_type

    def put_nowait(self, item: NoticeBase):
        super(NoticePriorityQueue, self).put_nowait(item)

    def put(self, item: NoticeBase, block=True, timeout=None):
        super(NoticePriorityQueue, self).put((item.level, item), block, timeout)

    def get(self, block=True, timeout=None):
        _, item = super(NoticePriorityQueue, self).get(block=block, timeout=timeout)
        return item

    def join(self):
        super(NoticePriorityQueue, self).join()


class NoticeQueue(object):
    def __init__(self):
        self.notification_queue = NoticePriorityQueue(notice_type=NoticeType.NOTIFICATION)
        self.data_queue = NoticePriorityQueue(notice_type=NoticeType.DATA)

    def put_nowait(self, item: NoticeBase):
        self.queue_type(item.type).put_nowait(item)

    def put(self, item: NoticeBase, block=True, timeout=None):
        self.queue_type(item.type).put(item, block, timeout)

    def get(self, notice_type: NoticeType, *args, **kwargs):
        return self.queue_type(notice_type).get(*args, **kwargs)

    def queue_type(self, notice_type: NoticeType):
        queue = None
        if notice_type == NoticeType.DATA:
            queue = self.data_queue
        elif notice_type == NoticeType.NOTIFICATION:
            queue = self.notification_queue

        return queue

    def join(self):
        self.notification_queue.join()
        self.data_queue.join()


class DataSenderNamespaceClient(BaseNamespace, Sender):
    def __init__(self, io, path):
        BaseNamespace.__init__(self, io, path)
        Sender.__init__(self)
        self.queue_data = Queue()
        self.device_up = False
        self.active = True
        self.size = 100
        self.id = 1

    def on_connect(self):
        logger.info('[Connected]')

    def on_reconnect(self):
        logger.info('[Reconnected]')

    def on_disconnect(self):
        self.device_up = False
        logger.info('[Disconnected]')

    def on_device_up(self):
        self.device_up = True
        self.emit('get_data', self.size)

    def on_new_data(self, items):
        """ Envía los datos recibidos desde el dispositivo y envía la confirmación recibida
            desde el servidor al dispositivo, para que marque el dato como envíado """

        self.queue_data.put_nowait(items)

    def process_data(self):
        while self.active:
            items = self.queue_data.get()

            if not items:
                break

            items_ok = []
            items_error = []

            for item in items:
                logger.info('[New data]')
                try:
                    self.send_data(item)
                    items_ok.append(item)
                except Exception:
                    logger.info("Error")
                    items_ok.append(item)

            self.emit('sended_data', items_ok, items_error)

        self.active = False


class WaitNoticeThread(Thread):
    def __init__(self, queue_data: NoticeQueue, db: DeviceDB, cls, emit):
        Thread.__init__(self)
        self.db = db
        self.cls = cls
        self.queue_data = queue_data
        self.emit = emit

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

    def on_sender_status(self, status):
        """ Evento que se recibe cuando el servicio de envío de datos cambia de estado """
        self.sender_up = status

    def on_sended_data(self, args):
        """ Marca los items como enviados correctamente, o incrementa el número de intentos en el caso de error """
        items = json.loads(args)

        self.update_status(items['items_ok'])
        self.update_status(items['items_fail'], False)
        self.sender_busy = False

    def update_status(self, items, status: bool = True):
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
        self.thread_wait_data = WaitNoticeThread(db=self.db, queue_data=self.queue_data, cls=self.cls, emit=self.emit)
        self.thread_wait_data.start()


class WaitNotificationThread(Thread):
    def __init__(self, queue_notification: NoticeQueue, level_notification, emit):
        Thread.__init__(self)
        self.queue_notification = queue_notification
        self.level_notification = level_notification
        self.emit = emit

    def run(self):
        """
        Envía los datos al servidor de notificaciones
        :return:
        """
        while True:
            item = self.queue_notification.get()
            if not item:
                break
            self.send_notification(item)
            self.queue_notification.task_done()

    def send_notification(self, notice: NoticeBase):
        """
        Envía la notificación al servidor, serializada en formato JSON
        :param notice: Notificación a enviar
        :return:
        """
        json_item = json.dumps(notice, sort_keys=True, cls=DataEncoder)
        if self.need_notification(notice):
            self.emit("new_notification", json_item)

    def need_notification(self, notice: Notification) -> bool:
        """
        Comprueba si la notificación necesita ser enviada al centro de
        notificaciones, dependiendo del nivel de la notificación
        :param notice: Notificación a comprobar
        :return: Si se envío o no (True|False)
        """
        return notice.level in self.level_notification


class NotificationNamespaceClient(BaseNamespace):
    """
    Permite el envío de notificaciones desde los clientes, se encarga
    de recibir los notificaciones a través de una cola y enviarlas
    al centro de notificaciones
    """
    def __init__(self, io, path):
        super(NotificationNamespaceClient, self).__init__(io, path)
        self.queue_notification = io.queue_notice.queue_type(NoticeType.NOTIFICATION)
        self.level_notification = io.level_notification
        self.thread_wait_notification = None

    def on_disconnect(self):
        """
        Cuando se desconecta el socket, se marca como inactivo, para
        evitar el envío de notificaciones al servidor
        :return:
        """
        self.queue_notification.put_nowait(None)

    def on_connect(self):
        """
        Activa el envío de notificaciones al servidor una vez se halla
        establecido la comunicación a través del socket
        :return:
        """
        self.thread_wait_notification = WaitNotificationThread(queue_notification=self.queue_notification,
                                                               level_notification=self.level_notification,
                                                               emit=self.emit)
        self.thread_wait_notification.start()


class NotificationThread(Thread):
    def __init__(self, queue_notice: NoticeQueue, db: DeviceDB, cls: BaseItem, **kwargs):
        super().__init__(**kwargs)

        self.queue_notice = queue_notice
        self.socket = None
        self.notification_namespace = None
        self.data_namespace = None
        self.db = db
        self.cls = cls
        self.level_notification = kwargs.pop('level_notification',
                                             [NotificationLevel.HIGHT, NotificationLevel.CRITICAL])

    def run(self):
        self.socket = SocketIO('127.0.0.1', 5000)
        self.socket.level_notification = self.level_notification
        self.socket.queue_notice = self.queue_notice
        self.socket.db = self.db
        self.socket.cls = self.cls
        self.data_namespace = self.socket.define(DataDeviceNamespaceClient, '/data')
        self.notification_namespace = self.socket.define(NotificationNamespaceClient, '/notifications')

        while True:
            pass


class NotificationClient(object):
    def __init__(self, db, cls):
        self.queues = {'notice': NoticeQueue()}

        self._notification_thread = NotificationThread(queue_notice=self.queues['notice'], db=db, cls=cls)
        self._notification_thread.start()

    def send_notification(self, notification: NoticeBase):
        logger.info(str(notification))
        self.queues['notice'].put_nowait(notification)
