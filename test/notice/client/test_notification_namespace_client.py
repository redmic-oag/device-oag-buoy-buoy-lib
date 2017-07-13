# -*- coding: utf-8 -*-

import unittest
import json

from nose.tools import eq_
from unittest.mock import patch

from buoy.lib.notification.client.common import NotificationNamespaceClient, NoticeQueue, WaitNotificationThread
from buoy.lib.notification.common import Notification, NotificationLevel, NoticeType
from buoy.lib.protocol.item import DataEncoder


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


class TestNotificationNamespaceClient(unittest.TestCase):

    def setUp(self):
        self.io = FakeIO()
        self.queue = self.io.queue_notice.queue_type(NoticeType.NOTIFICATION)
        self.device_id = "PB200"
        self.namespace = NotificationNamespaceClient(self.io, '/data')
        self.namespace.device_id = self.device_id

    @patch.object(WaitNotificationThread, 'is_active', return_value=AlmostAlwaysTrue(1))
    @patch.object(WaitNotificationThread, 'emit')
    def test_should_noEmitEventNewNotification_when_addNotificationNormal(self, mock_emit, mock_is_active):
        item = Notification(level=NotificationLevel.NORMAL, message="Hola", phone="1234")

        self.queue.put_nowait(item)
        self.namespace.on_connect()
        eq_(mock_emit.call_count, 0)

    @patch.object(WaitNotificationThread, 'is_active', return_value=AlmostAlwaysTrue(1))
    @patch.object(WaitNotificationThread, 'emit')
    def test_should_emitEventNewNotification_when_addNotificationCritical(self, mock_emit, mock_is_active):
        item = Notification(level=NotificationLevel.CRITICAL, message="Hola", phone="1234")
        json_expected = json.dumps(item, sort_keys=True, cls=DataEncoder)

        self.queue.put_nowait(item)
        self.namespace.on_connect()

        eq_(mock_emit.call_count, 1)
        mock_emit.assert_called_once_with("new_notification", json_expected)
