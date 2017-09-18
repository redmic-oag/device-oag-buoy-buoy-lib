# -*- coding: utf-8 -*-

import unittest
import json

from nose.tools import eq_
from unittest.mock import patch, MagicMock

from buoy.lib.notification.server import NotificationNamespace, NotificationDB
from buoy.lib.notification.common import Notification, NotificationLevel
from buoy.lib.protocol.item import DataEncoder


class FakeNotificationDB(NotificationDB):
    def __init__(self):
        pass


class TestNotificationNamespaceServer(unittest.TestCase):

    def setUp(self):
        self.db_config = {
            'database': 'boyadb',
            'user': 'boya',
            'password': 'b0y4_04G',
            'host': '127.0.0.1'
        }

    @patch('buoy.lib.notification.server.NotificationDB')
    @patch('buoy.lib.notification.server.emit')
    def test_should_emitEventSendNotification_when_receivedNewNotification(self, mock_emit, mock_db):
        data = {
            'level': NotificationLevel.CRITICAL,
            'message': "Hola",
            'phone': "1234",
            'daemon': 'sms-cli'
        }

        notification = Notification(**data)
        namespace = NotificationNamespace(namespace="/notification", db_config=self.db_config)
        namespace.db.save = MagicMock(return_value=notification)

        json_expected = json.dumps(notification, sort_keys=True, cls=DataEncoder)
        namespace.on_new_notification(json_expected)

        eq_(mock_emit.call_count, 1)
        mock_emit.assert_called_once_with("send_notification", json_expected)

