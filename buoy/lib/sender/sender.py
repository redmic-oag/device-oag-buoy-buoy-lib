# -*- coding: utf-8 -*-

import json
import time
import logging

from requests import post
from requests.exceptions import ConnectionError

from buoy.lib.protocol.item import DataEncoder
from buoy.lib.device.database import DeviceDB
from buoy.lib.service.daemon import Daemon

logger = logging.getLogger(__name__)


class NoConnectionToServerException(Exception):
    pass


class ErrorSendDataToServerException(Exception):
    pass


class ErrorIdsResponseServerException(Exception):
    pass


class Sender(object):
    def __init__(self):
        self.headers = {'content-type': 'application/json'}

    def send_data(self, url, item):
        """
            400 - Parámetros no corresponden - Bad request
            403 - Sin permisos
            500 - Error en el server
        """

        json_to_send = json.dumps(item, sort_keys=True, cls=DataEncoder)
        try:
            response = post(url, data=json_to_send, headers=self.headers)
        except ConnectionError as e:
            raise NoConnectionToServerException()

        if response.status_code > 200:
            if response.status_code == 404:
                raise NoConnectionToServerException()
            else:
                raise ErrorSendDataToServerException()

        return True


class DaemonSend(Daemon):
    def __init__(self, name, **kwargs) -> None:
        Daemon.__init__(self, name + "_sender", daemon_config=kwargs.pop("service_config"))
        self.db = DeviceDB(db_config=kwargs.pop("db_config"), db_tablename=name)
        sender_config = kwargs.pop("sender_config")
        self.timeout = sender_config["timeout"]
        self.element_to_send = sender_config["element_to_send"]
        self.cls = kwargs.pop("cls")
        self.url = sender_config["url"]

        self.sender = Sender()

    def start(self, debug=False):
        while self.status:
            items = self.db.get_items_to_send(cls=self.cls, size=self.element_to_send)
            if len(items):
                try:
                    resp = self.sender.send(self.url, items)
                    self.db.update_status(resp['ok'])
                    self.db.update_status(resp['fail'], False)
                    logger.info("Items sent ok: {ok}, fail: {fail}".format(**resp))
                except (ConnectionError, NoConnectionToServerException, ErrorSendDataToServerException) as e:
                    logger.warning("Server not respond")
                    self.wait(debug)
                except ErrorIdsResponseServerException as e:
                    logger.warning("Server response contains ids not sent")

            else:
                logger.info("There are no new items to send")
                self.wait(debug)

        if not debug:
            self.stop()

    def wait(self, debug):
        if not debug:
            time.sleep(self.timeout)
        else:
            self.status = False
