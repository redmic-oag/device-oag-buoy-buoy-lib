import unittest

from nose.tools import eq_
from unittest.mock import patch, Mock, call

from datetime import datetime, timezone
from queue import Queue
from buoy.lib.device.base import ItemSaveThread
from buoy.lib.notification.client import NoticeQueue
from buoy.lib.notification.common import NoticeType
from buoy.lib.protocol.nmea0183 import WIMDA


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


class TestItemSaveThread(unittest.TestCase):

    @patch('buoy.lib.device.base.ItemSaveThread.save')
    @patch('buoy.lib.device.base.DeviceDB', return_value=Mock())
    def test_twiceCallSaveMethodAndExitsTwoItemsInNoticeQueue_when_insertTwoItemsInQueueData(self,
                                                                                             mock_device, mock_save):
        queue_data = Queue()
        queue_notice = NoticeQueue()

        items_expected = []
        for item in get_items(2):
            queue_data.put_nowait(item)
            items_expected.append(call(item))

        queue_data.put_nowait(None)

        thread = ItemSaveThread(queue_save_data=queue_data, queue_notice=queue_notice)
        thread.run()

        eq_(queue_notice.queue_type(NoticeType.DATA).qsize(), 2)
        eq_(mock_save.call_count, 2)
        eq_(mock_save.call_args_list, items_expected)


if __name__ == '__main__':
    unittest.main()
