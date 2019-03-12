import unittest
from queue import Queue
from unittest.mock import patch, call

from nose.tools import eq_

from buoy.base.data.item import ItemQueue, Status
from buoy.base.device.threads.save import SaveThread


def get_item():
    pass


def get_items(num=2):
    items = []
    for i in range(0, num):
        items.append(get_item())
    return items


class ItemSaveThreadTest(unittest.TestCase):
    __test__ = False

    @patch.object(SaveThread, 'save')
    @patch.object(SaveThread, 'set_sent')
    @patch.object(SaveThread, 'set_failed')
    @patch.object(SaveThread, 'is_active', side_effect=[True, True, True, False])
    def test_callActionDb_when_insertItemsWithVariousStatusInQueueData(self, mock_is_active, mock_set_failed,
                                                                       mock_set_sent, mock_save):
        queue_data = Queue()
        queue_notice = Queue()

        items = [ItemQueue(data=get_item()), ItemQueue(data=get_item(), status=Status.SENT),
                 ItemQueue(data=get_item(), status=Status.FAILED)]

        for item in items:
            queue_data.put_nowait(item)

        thread = SaveThread(queue_save_data=queue_data, db=None, queue_notice=queue_notice)
        thread.run()

        eq_(mock_is_active.call_count, 4)
        eq_(mock_save.call_count, 1)
        eq_(mock_save.call_args, call(items[0].data))
        eq_(mock_set_sent.call_args, call(items[1].data))
        eq_(mock_set_failed.call_args, call(items[2].data))
