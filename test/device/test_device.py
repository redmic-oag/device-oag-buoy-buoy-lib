import unittest

from nose.tools import eq_
from unittest.mock import patch
from serial import SerialException

from buoy.lib.device.base import Device, DeviceNoDetectedException


class TestDevice(unittest.TestCase):

    @patch('buoy.lib.device.base.Serial', side_effect=SerialException())
    @patch.object(Device, 'send_notification', return_value=None)
    def test_hould_return_exception_when_the_device_is_not_present(self, mock_send_notification, mock_serial):

        db_config = {
            'database': 'boyadb',
            'user': 'boya',
            'password': 'b0y4_04G',
            'host': '127.0.0.1'
        }

        serial_config = {
            'port': '/dev/weather_station',
            'baudrate': 4800,
            'stopbits': 1,
            'parity': 'N',
            'bytesize': 8,
            'timeout': 0
        }

        device = Device(device_name="test", db_config=db_config, serial_config=serial_config)

        self.assertRaises(DeviceNoDetectedException, device.connect)
        eq_(mock_send_notification.call_count, 1)


if __name__ == '__main__':
    unittest.main()
