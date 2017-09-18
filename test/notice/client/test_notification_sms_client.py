# -*- coding: utf-8 -*-

import unittest
import json

from nose.tools import eq_
from unittest.mock import patch, MagicMock, call

from queue import PriorityQueue

from buoy.lib.notification.client.common import NoticeQueue
from buoy.lib.notification.client.sender import WaitSMSThread
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


class WaitSMSThreadTest(unittest.TestCase):

    def setUp(self):
        self.queue = PriorityQueue()
        self.phone_alert = "+34660046155"
        self.thread = WaitSMSThread(queue_notification=self.queue, phone_alert=self.phone_alert, emit=None)

    @patch('buoy.lib.notification.client.sender.sms_send',  return_value=True)
    def test_should_sendSMStoPhoneAlert_when_passNotificationUnfilledPhone(self, mock_sms_send):
        message = "Prueba"
        notification = Notification(message=message, level=NotificationLevel.NORMAL)
        self.thread.send_sms(notification)

        eq_(mock_sms_send.call_count, 1)
        eq_(mock_sms_send.call_args, call(self.phone_alert, message))

    @patch('buoy.lib.notification.client.sender.sms_send',  return_value=True)
    def test_should_sendSMStoPhoneAlert_when_passNotificationFilledPhone(self, mock_sms_send):
        message = "Prueba"
        phone = "+34660045156"
        notification = Notification(message=message, level=NotificationLevel.NORMAL, phone=phone)
        self.thread.send_sms(notification)

        eq_(mock_sms_send.call_count, 1)
        eq_(mock_sms_send.call_args, call(phone, message))

    @patch('buoy.lib.notification.client.sender.sms_send',  return_value=True)
    def test_should_noSendSMS_when_passNotificationUnfilledMessage(self, mock_sms_send):
        phone = "+34660045156"
        notification = Notification(None, level=NotificationLevel.NORMAL, phone=phone)
        self.thread.send_sms(notification)

        eq_(mock_sms_send.call_count, 0)




