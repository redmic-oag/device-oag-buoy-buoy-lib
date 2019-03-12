# -*- coding: utf-8 -*-

import logging
from queue import Queue, Empty

from buoy.base.data.item import Status
from buoy.base.database import DeviceDB
from buoy.base.device.threads.base import BaseThread

logger = logging.getLogger(__name__)


class SaveThread(BaseThread):
    """
    Clase encargada de guardar los datos en la base de datos
    """

    def __init__(self, db: DeviceDB, queue_save_data: Queue, queue_notice: Queue):
        super(SaveThread, self).__init__(queue_notice)
        self.db = db
        self.queue_save_data = queue_save_data

    def activity(self):
        try:
            item = self.queue_save_data.get(timeout=self.timeout_wait)

            if item.status == Status.NEW:
                self.save(item.data)
                # TODO Habría que tener encuenta si el item se guardó antes
            elif item.status == Status.SENT:
                self.set_sent(item.data)
                # TODO Habría que tener encuenta si el item no existe
            elif item.status == Status.FAILED:
                self.set_failed(item.data)

            self.queue_save_data.task_done()
        except Empty:
            pass

    def save(self, item):
        """ Guarda el registro en la base de datos """
        logger.debug("Save to item %s" % str(item))
        self.db.save(item)

    def set_sent(self, item):
        logger.debug("Mark item with sent %s" % str(item))
        self.db.set_sent(item.uuid)

    def set_failed(self, item):
        logger.debug("Mark item with send failed %s" % str(item))
        self.db.set_failed(item.uuid)
