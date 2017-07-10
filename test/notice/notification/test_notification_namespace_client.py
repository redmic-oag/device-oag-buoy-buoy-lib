# -*- coding: utf-8 -*-

import unittest
import json

from datetime import datetime, timezone
from nose.tools import eq_, ok_
from unittest.mock import patch, MagicMock, call

from buoy.lib.notification.client import NotificationNamespaceClient, NoticeQueue
from buoy.lib.notification.common import Notification, NotificationLevel, NoticeType
from buoy.lib.protocol.nmea0183 import WIMDA
from buoy.lib.device.database import DeviceDB
from buoy.lib.protocol.item import DataEncoder


def get_items(num=1):
    items = []
    for i in range(0, num):
        data = {
            'id': i,
            'datetime': datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f%z"),
            'air_temperature': '26.8',
            'barometric_pressure_inch': '30.3273',
            'barometric_pressure_bar': '1.027',
            'water_temperature': '20.1',
            'relative_humidity': '12.3',
            'absolute_humidity': '21.0',
            'dew_point': '2.3',
            'wind_direction_true': '2.0',
            'wind_direction_magnetic': '128.7',
            'wind_speed_knots': '134.6',
            'wind_speed_meters': '0.3'
        }

        items.append(WIMDA(**data))

    return items

class AlmostAlwaysTrue(object):
    def __init__(self, total_iterations=1):
        self.total_iterations = total_iterations
        self.current_iteration = 0

    def __nonzero__(self):
        if self.current_iteration < self.total_iterations:
            self.current_iteration += 1
            return bool(1)
        return bool(0)

    # Python >= 3
    def __bool__(self):
        if self.current_iteration < self.total_iterations:
            self.current_iteration += 1
            return bool(1)
        return bool(0)


class FakeIO(object):
    def __init__(self):
        self._url = 'http://redmic.es'
        self.queue_notice = NoticeQueue()
        self.level_notification = [NotificationLevel.CRITICAL]


class TestDataDeviceNamespaceClient(unittest.TestCase):

    def setUp(self):
        self.io = FakeIO()
        self.queue = self.io.queue_notice.queue_type(NoticeType.NOTIFICATION)
        self.device_id = "PB200"
        self.namespace = NotificationNamespaceClient(self.io, '/data')
        self.namespace.device_id = self.device_id


    @patch('buoy.lib.notification.client.NotificationNamespaceClient.emit')
    def test_should_EmitEventAddDevice_when_connectToServer(self, mock_emit):
        self.namespace.is_active = MagicMock(return_value=AlmostAlwaysTrue(1))
        item = Notification(level=NotificationLevel.CRITICAL, message="Hola", phone="1234")

        self.queue.put_nowait(item)
        self.namespace.on_connect()

        eq_(mock_emit.call_count, 1)
        mock_emit.assert_called_once_with("new_notification", self.device_id)

