import unittest

from nose.tools import eq_
from unittest.mock import patch
from serial import SerialException

from buoy.lib.device.base import Device, DeviceNoDetectedException


class TestDevice(unittest.TestCase):

    @patch('buoy.lib.device.base.Serial', side_effect=SerialException())
    @patch.object(Device, 'send_notification', return_value=None)
    def test_shouldReturnException_when_theDeviceIsNotPresent(self, mock_send_notification, mock_serial):

        serial_config = {
            'port': '/dev/weather_station',
            'baudrate': 4800,
            'stopbits': 1,
            'parity': 'N',
            'bytesize': 8,
            'timeout': 0
        }

        device = Device(device_name="test", db=None, serial_config=serial_config)

        self.assertRaises(DeviceNoDetectedException, device.connect)
        eq_(mock_send_notification.call_count, 1)


if __name__ == '__main__':
    unittest.main()
