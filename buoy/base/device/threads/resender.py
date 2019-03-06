# -*- coding: utf-8 -*-

import logging
from queue import Queue, Full

from buoy.base.database import DeviceDB
from buoy.base.device.threads.base import BaseThread

logger = logging.getLogger(__name__)


class DBToSendThread(BaseThread):
    """
    Clase base encargada buscar datos en la base de datos que no han sido enviados
    """

    def __init__(self, db: DeviceDB, queue_send_data: Queue, queue_notice: Queue, **kwargs):
        super(DBToSendThread, self).__init__(queue_notice,
                                             timeout_wait=kwargs.pop('timeout_wait', 300))

        self.db = db
        self.queue_send_data = queue_send_data
        self.queue_notice = queue_notice
        self.limit_queue = kwargs.pop("limit_queue", 100)

    def activity(self):
        if not self.queue_send_data.full():
            items = self.db.get_items_to_send()
            for item in items:
                try:
                    self.queue_send_data.put_nowait(item)
                except Full:
                    logger.warning("Send queue is full")
                    break
