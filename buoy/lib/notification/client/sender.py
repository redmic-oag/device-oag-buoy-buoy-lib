# -*- coding: utf-8 -*-

import logging

from threading import Thread
from queue import PriorityQueue
from socketIO_client import BaseNamespace
from vodem.simple import sms_send

from buoy.lib.notification.common import NoticeType, Notification

logger = logging.getLogger(__name__)


class WaitSMSThread(Thread):
    def __init__(self, queue_notification: PriorityQueue, phone_alert: str, emit):
        Thread.__init__(self)
        self.queue_notification = queue_notification
        self._emit = emit
        self._active = False
        self.phone_alert = phone_alert

    def run(self):
        """
        Envía los datos al servidor de notificaciones
        :return:
        """
        self._active = True
        while self.is_active():
            item = self.queue_notification.get()
            self.send_notification(item)
            self.queue_notification.task_done()

    def is_active(self):
        return self._active

    def send_notification(self, notification: Notification):
        """
        Envía la notificación al servidor, serializada en formato JSON
        :param notification: Notificación a enviar
        :return:
        """
        self.send_sms(notification)
        self.emit("sended_notification", notification.to_json())

    def send_sms(self, notification: Notification):

        if notification and notification.message:
            phone = self.phone_alert
            if notification.phone:
                phone = notification.phone

            sms_send(phone, notification.message)
            logger.info("Send SMS %s content %s" % (phone, notification.message, ))

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
        self.active = False
        self.thread_wait_notification = None
        self.target_id = "SMS"

    def on_connect(self):
        """
        Activa el envío de notificaciones al servidor una vez se halla
        establecido la comunicación a través del socket
        :return:
        """
        self.thread_wait_notification = WaitSMSThread(queue_notification=self.queue_notification,
                                                      emit=self.emit)
        self.thread_wait_notification.start()

    def on_disconnect(self):
        """
        Cuando se desconecta el socket, se marca como inactivo, para
        evitar el envío de notificaciones al servidor
        :return:
        """
        if self.thread_wait_notification and self.thread_wait_notification.is_alive():
            self.thread_wait_notification.stop()
