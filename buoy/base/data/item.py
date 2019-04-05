# -*- coding: utf-8 -*-

import json
import logging
from datetime import datetime, timezone, timedelta
from decimal import *
from enum import Enum
from uuid import uuid4, UUID
from buoy.base.data.utils import convert_to_seconds, round_time

from dateutil import parser

logger = logging.getLogger(__name__)


class BaseItem(object):
    def __init__(self, **kwargs):
        self.uuid = kwargs.pop('uuid', uuid4())
        self.date = kwargs.pop('date', datetime.now(tz=timezone.utc))

    @property
    def uuid(self):
        """
        :return: Identifier
        :rtype: Integer
        """
        return self._uuid

    @uuid.setter
    def uuid(self, value):
        self._uuid = value

    @property
    def date(self):
        """
        :return: Datetime
        :rtype: Datetime
        """
        return self._date

    @date.setter
    def date(self, value):
        if type(value) is int:
            value = datetime.fromtimestamp(value / 1000.0)
        elif type(value) is str:
            value = parser.parse(value)

        self._date = value

    @staticmethod
    def _convert_string_to_decimal(value):
        val = None
        if value is not None:
            try:
                val = Decimal(value)
            except InvalidOperation:
                logger.error("Convert string to decimal", value)

        return val

    def to_json(self):
        item = json.dumps(self, cls=DataEncoder, sort_keys=True, separators=(',', ':'))
        return item

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
            a = dict(other)
            b = dict(self)
            return a == b
        return False

    def __lt__(self, other):
        if isinstance(other, self.__class__):
            return self.date < other.date

    def __str__(self):
        return ("Uuid: {uuid}\n"
                "Date: {date}\n").format(**dict(self))

    def __copy__(self):
        cls = self.__class__
        result = cls.__new__(cls)
        result.__dict__.update(self.__dict__)
        return result


class DataEncoder(json.JSONEncoder):
    def default(self, o):
        serial = {}
        for name in dir(o):
            value = getattr(o, name)
            datatype = type(value)
            if datatype is datetime:
                serial[name] = value.isoformat(timespec='milliseconds')
            elif datatype is Decimal:
                serial[name] = round(float(value), 3)
            elif datatype is int:
                serial[name] = value
            elif datatype is str:
                serial[name] = value
            elif datatype is UUID:
                serial[name] = str(value)
            elif isinstance(value, BaseItem):
                serial[name] = self.default(value)
            elif value:
                try:
                    serial[name] = json.JSONEncoder.default(self, value)
                except TypeError as e:
                    logger.error("No serialize property %s with value %s" % (name, value,))

        return serial


class Status(Enum):
    NEW = 0
    SENT = 1
    FAILED = 2


class ItemQueue(object):
    def __init__(self, data: BaseItem, **kwargs):
        self.status = kwargs.pop("status", Status.NEW)
        self.data = data


class BufferItems(object):
    def __init__(self, **kwargs):
        self.__buffer = []
        self.interval = kwargs.pop("interval", None)
        if self.interval:
            self.interval = convert_to_seconds(self.interval)

        self.__limit_higher = None
        self.__limit_lower = None

        self.__item_cls = None
        self.__fields = None

    @staticmethod
    def extract_fieldname_parameters(item):
        return list(set(dir(item)) - set(dir(BaseItem)))

    def append(self, other: BaseItem):
        item = None

        if other is None:
            return item

        if self.interval is None:
            item = other
        elif self.inside_interval(other.date):
            if len(self.__buffer) == 0:
                if self.__fields is None and self.__item_cls is None:
                    self.__item_cls = type(other)
                    self.__fields = self.extract_fieldname_parameters(other)

                self.set_limits(other.date)
            logger.debug("Inserting item in buffer")
            self.__buffer.append(other)
        else:
            item = self.process_buffer()
            self.clear()
            self.append(other)

        return item

    def set_limits(self, date):
        logger.debug("Setting limits %s", str(date))
        logger.debug("Interval %i", self.interval)
        self.__limit_lower = round_time(dt=date, round_to=self.interval, to="down")
        self.__limit_higher = self.__limit_lower + timedelta(seconds=self.interval)
        logger.debug("Set limits lower: %s", str(self.__limit_lower))

    def clear(self):
        self.__buffer.clear()
        self.__limit_lower = None
        self.__limit_higher = None

    def limits(self):
        return self.__limit_lower, self.__limit_higher

    def inside_interval(self, date):
        return self.__limit_higher is None and self.__limit_lower is None or \
               (self.__limit_lower < date <= self.__limit_higher)

    def process_buffer(self):
        logger.debug("Proccesing buffer %i", len(self.__buffer))
        logger.debug("Fieldnames: %s", " , ".join(self.__fields))
        item_attr = {
            "date": self.__limit_higher
        }
        for key in self.__fields:
            attr = [getattr(o, key) for o in self.__buffer if getattr(o, key)]
            if len(attr) > 0:
                item_attr[key] = sum(attr) / len(attr)
            else:
                item_attr[key] = None

        logger.debug("Item processed")
        return self.__item_cls(**item_attr)
