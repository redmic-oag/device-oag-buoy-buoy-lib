import unittest
from datetime import datetime, timezone
from queue import Queue
from unittest.mock import patch, call

from nose.tools import eq_

from buoy.client.device.common.item import ItemQueue, Status
from buoy.client.device.common.base import ItemSaveThread
from buoy.client.device.common.nmea0183 import WIMDA


def get_item():
    data = {
        'date': datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f%z"),
        'air_temp': '26.8',
        'press_inch': '30.3273',
        'pres_mbar': '1.027',
        'water_temp': '20.1',
        'rel_humidity': '12.3',
        'abs_humidity': '21.0',
        'dew_point': '2.3',
        'wind_dir_true': '2.0',
        'wind_dir_magnetic': '128.7',
        'wind_knots': '134.6',
        'wind_meters': '0.3'
    }
    return WIMDA(**data)


def get_items(num=2):
    items = []
    for i in range(0, num):
        items.append(get_item())
    return items


class TestItemSaveThread(unittest.TestCase):
    @patch.object(ItemSaveThread, 'save')
    @patch.object(ItemSaveThread, 'set_sent')
    @patch.object(ItemSaveThread, 'set_failed')
    @patch.object(ItemSaveThread, 'is_active', side_effect=[True, True, True, False])
    def test_callActionDb_when_insertItemsWithVariousStatusInQueueData(self, mock_is_active, mock_set_failed,
                                                                       mock_set_sent, mock_save):
        queue_data = Queue()
        queue_notice = Queue()

        items = [ItemQueue(data=get_item()), ItemQueue(data=get_item(), status=Status.SENT),
                 ItemQueue(data=get_item(), status=Status.FAILED)]

        for item in items:
            queue_data.put_nowait(item)

        thread = ItemSaveThread(queue_save_data=queue_data, db=None, queue_notice=queue_notice)
        thread.run()

        eq_(mock_is_active.call_count, 4)
        eq_(mock_save.call_count, 1)
        eq_(mock_save.call_args, call(items[0].data))
        eq_(mock_set_sent.call_args, call(items[1].data))
        eq_(mock_set_failed.call_args, call(items[2].data))


if __name__ == '__main__':
    unittest.main()
