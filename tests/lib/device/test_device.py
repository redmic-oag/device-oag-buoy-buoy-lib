import unittest
from unittest.mock import patch

from serial import SerialException

from buoy.base.device.device import Device
from buoy.base.device.exceptions import DeviceNoDetectedException


class TestDevice(unittest.TestCase):

    # TODO arreglar test
    @unittest.skip
    @patch('buoy.lib.device.device.Serial', side_effect=SerialException())
    def test_shouldReturnException_when_theDeviceIsNotPresent(self, mock_serial):
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

    @patch.object(Device, 'is_open', return_value=True)
    def test_shouldReturnException_when_existsExceptionsInQueue(self, mock_is_open):
        ex = DeviceNoDetectedException(exception=Exception())
        serial_config = {
            'port': '/dev/weather_station',
            'baudrate': 4800,
            'stopbits': 1,
            'parity': 'N',
            'bytesize': 8,
            'timeout': 0
        }

        device = Device(device_name="test", db=None, serial_config=serial_config)
        device.queues['notice'].put_nowait(ex)

        self.assertRaises(DeviceNoDetectedException, device._listener_exceptions)


if __name__ == '__main__':
    unittest.main()
