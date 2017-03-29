# -*- coding: utf-8 -*-

import json
import logging
from datetime import datetime
from decimal import *

logger = logging.getLogger(__name__)


class BaseItem(object):
    def __init__(self, **kwargs):
        self.id = kwargs.pop('id', None)
        self.datetime = kwargs.pop('datetime', None)

    @property
    def id(self):
        """
        :return: Identifier
        :rtype: Integer
        """
        return self._id

    @id.setter
    def id(self, value):
        self._id = value

    @property
    def datetime(self):
        """
        :return: Datetime
        :rtype: Datetime
        """
        return self._datetime

    @datetime.setter
    def datetime(self, value):
        self._datetime = value

    @staticmethod
    def _convert_string_to_decimal(value):
        val = None
        if value is not None:
            try:
                val = Decimal(value)
            except InvalidOperation:
                # TODO Lanzar mensajes al log
                logger.error("Convert string to decimal", value)

        return val

    def __iter__(self):
        for name in dir(self):
            yield name, getattr(self, name)

    def __dir__(self):
        list_props = []
        for name in vars(self):
            list_props.append(name[1:])

        return list_props

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return dict(self) == dict(other)
        return False


class DataEncoder(json.JSONEncoder):
    def default(self, o):
        serial = {}
        for name in dir(o):
            value = getattr(o, name)
            if type(value) is datetime:
                serial[name] = value.strftime("%Y-%m-%dT%H:%M:%S.%f%z")
            elif type(value) is Decimal:
                serial[name] = float(value)
            elif type(value) is int:
                serial[name] = value
            elif value:
                try:
                    serial[name] = json.JSONEncoder.default(self, value)
                except TypeError:
                    logger.error("No serialize property %s with value %s" % (name, value,))

        return serial
