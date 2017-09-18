import unittest

from nose.tools import eq_, ok_
from unittest.mock import patch

from datetime import datetime, timezone

from buoy.lib.protocol.nmea0183 import WIMDA
from buoy.lib.sender.sender import Sender, NoConnectionToServerException, ErrorSendDataToServerException
from buoy.lib.notification.client.common import NoticeQueue
from buoy.lib.notification.client.device import DataDeviceNamespaceClient


class FakeResponse:
    def __init__(self, **kwargs):
        self.content = str.encode(kwargs.pop('content', ""))
        self.status_code = kwargs.pop('status_code', 200)


class TestDataSenderNamespaceClient(unittest.TestCase):
    def setUp(self):

        self.url = 'https://redmic.es/activity/1/device/2fsafsdfka/data'
        self.data = {
            'id': None,
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

        self.item = WIMDA(**self.data)

    @patch('buoy.lib.sender.sender.post', return_value=FakeResponse(content=''))
    def test_should_return_true_when_response_at_request_post_is_200(self, mock_post):
        sender = Sender()

        ok_(sender.send_data(self.url, self.item), True)

    @patch('buoy.lib.sender.sender.post', return_value=FakeResponse(content='', status_code=404))
    def test_should_raise_NoConnectionToServerException_when_response_at_request_post_is_404(self, mock_post):
        sender = Sender()

        self.assertRaises(NoConnectionToServerException, sender.send_data, self.url, self.item)

    @patch('buoy.lib.sender.sender.post', return_value=FakeResponse(content='', status_code=209))
    def test_should_raise_ErrorSendDataToServerException_when_response_at_request_post_is_209(self, mock_post):
        sender = Sender()

        self.assertRaises(ErrorSendDataToServerException, sender.send_data, self.url, self.item)

    @patch.object('buoy.lib.notification.client.common.BaseNamespace.emit')
    @patch('buoy.lib.sender.sender.Sender.send_data', return_value=True)
    def test_should_calledOnceMethodSendData_when_eventOnNewDataIsReceived(self, mock_send_data, mock_emit):
        class FakeIO(object):
            def __init__(self):
                self._url = 'http://redmic.es'
                self.queue_notice = NoticeQueue()

        io = FakeIO()
        namespace = DataDeviceNamespaceClient(io, '/data')
        items = []
        for i in range(10):
            items.append(self.item)

        namespace.queue_data.put_nowait(items)
        namespace.queue_data.put_nowait(None)

        namespace.process_data()
        mock_send_data.call_count = len(items)
        mock_emit.assert_called_once_with('sended_data', items, [])
