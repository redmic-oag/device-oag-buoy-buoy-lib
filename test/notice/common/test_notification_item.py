import unittest

from nose.tools import eq_

from buoy.lib.notification.common import Notification, NotificationLevel
from buoy.lib.notification.exceptions import ValidationError


class TestNotificationItem(unittest.TestCase):
    def test_should_return_equals_values_to_data(self):
        data = {
            'level': NotificationLevel.CRITICAL,
            'message': "Hola",
            'phone': "1234"
        }

        item = Notification(level=NotificationLevel.CRITICAL, message="Hola", phone="1234")

        for key, value in data.items():
            eq_(getattr(item, key), value)

    def test_should_return_exception_when_phone_is_invalid_number(self):
        self.assertRaises(ValidationError, Notification.validate_mobile, "123445")

    def test_should(self):
        data = {'level': 1, 'message': 'Device no detected', 'datetime': '2017-06-22T09:57:39.204529+0000', 'type': 1}

        notification = Notification(**data)
        for k, v in data.items():
            eq_(getattr(notification, k), v)

if __name__ == '__main__':
    unittest.main()
