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
        if type(value) is int:
            value = datetime.fromtimestamp(value/1000.0)

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

    def __lt__(self, other):
        if isinstance(other, self.__class__):
            return self.datetime < other.datetime

    def __str__(self):
        line = ''
        for name in dir(self):
            line += '%s: %s | ' % (name, getattr(self, name))


class DataEncoder(json.JSONEncoder):
    def default(self, o):
        serial = {}
        for name in dir(o):
            value = getattr(o, name)
            datatype = type(value)
            if datatype is datetime:
                serial[name] = value.strftime("%Y-%m-%dT%H:%M:%S.%f%z")
            elif datatype is Decimal:
                serial[name] = float(value)
            elif datatype is int:
                serial[name] = value
            elif datatype is str:
                serial[name] = value
            elif isinstance(value, BaseItem):
                serial[name] = self.default(value)
            elif value:
                try:
                    serial[name] = json.JSONEncoder.default(self, value)
                except TypeError as e:
                    logger.error("No serialize property %s with value %s" % (name, value,))

        return serial
