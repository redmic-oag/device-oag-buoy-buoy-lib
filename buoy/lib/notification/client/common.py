# -*- coding: utf-8 -*-

import logging
import json

from threading import Thread
from queue import PriorityQueue
from socketIO_client import SocketIO, BaseNamespace

from buoy.lib.notification.common import NoticeBase, NotificationLevel, NoticeType
from buoy.lib.notification.common import Notification
from buoy.lib.protocol.item import DataEncoder

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


class WaitNotificationThread(Thread):
    def __init__(self, queue_notification: NoticeQueue, level_notification, emit):
        Thread.__init__(self)
        self.queue_notification = queue_notification
        self.level_notification = level_notification
        self._emit = emit
        self._active = False

    def run(self):
        """
        Envía los datos al servidor de notificaciones
        :return:
        """
        self._active = True
        while self.is_active():
            item = self.queue_notification.get()
            if self.need_notification(item):
                self.send_notification(item)
            self.queue_notification.task_done()

    def is_active(self):
        return self._active

    def need_notification(self, notice: Notification) -> bool:
        """
        Comprueba si la notificación necesita ser enviada al centro de
        notificaciones, dependiendo del nivel de la notificación
        :param notice: Notificación a comprobar
        :return: Si se envío o no (True|False)
        """
        return notice.level in self.level_notification

    def send_notification(self, notice: NoticeBase):
        """
        Envía la notificación al servidor, serializada en formato JSON
        :param notice: Notificación a enviar
        :return:
        """
        json_item = json.dumps(notice, sort_keys=True, cls=DataEncoder)
        self.emit("new_notification", json_item)

    def emit(self, event: str, data):
        self._emit(event, data)

    def stop(self):
        self._active = False
        self.join()


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
        self.active = False
        self.thread_wait_notification = None

    def on_disconnect(self):
        """
        Cuando se desconecta el socket, se marca como inactivo, para
        evitar el envío de notificaciones al servidor
        :return:
        """
        if self.thread_wait_notification and self.thread_wait_notification.is_alive():
            self.thread_wait_notification.stop()

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
    def __init__(self, queue_notice: NoticeQueue, **kwargs):
        super().__init__(**kwargs)

        self.queue_notice = queue_notice
        self.socket = None
        self.notification_namespace = None
        self.level_notification = kwargs.pop('level_notification',
                                             [NotificationLevel.HIGHT, NotificationLevel.CRITICAL])

    def run(self):
        self.prepare_sockect()
        self.socket.wait()

    def prepare_sockect(self):
        self.socket = SocketIO('127.0.0.1', 5000)
        self.socket.level_notification = self.level_notification
        self.socket.queue_notice = self.queue_notice
        self.notification_namespace = self.socket.define(NotificationNamespaceClient, '/notifications')
