import unittest

from nose.tools import eq_

from buoy.lib.notification.client import NoticePriorityQueue, NoticeQueue
from buoy.lib.notification.common import Notification, NotificationLevel, NoticeType


class TestNoticePriorityQueue(unittest.TestCase):
    def test_should_return_notification_sorted_by_priority(self):
        item1 = Notification(level=NotificationLevel.LOW, message="1", phone="1234")
        item2 = Notification(level=NotificationLevel.CRITICAL, message="2", phone="1234")
        item3 = Notification(level=NotificationLevel.NORMAL, message="3", phone="1234")

        queue = NoticePriorityQueue(notice_type=NoticeType.NOTIFICATION)
        queue.put_nowait(item1)
        queue.put_nowait(item2)
        queue.put_nowait(item3)

        eq_(queue.get(), item2)
        eq_(queue.get(), item3)
        eq_(queue.get(), item1)

    def test_should_return_specific_queue_when_send_type_notice(self):
        queue = NoticeQueue()

        eq_(queue.queue_type(NoticeType.DATA).type, NoticeType.DATA)
        eq_(queue.queue_type(NoticeType.NOTIFICATION).type, NoticeType.NOTIFICATION)

    def test_should_return_specific_queue_when_send_type_notice(self):
        queue = NoticeQueue()

        item = Notification(level=NotificationLevel.LOW, message="1", phone="1234")
        queue.put_nowait(item)

        eq_(queue.queue_type(NoticeType.NOTIFICATION).qsize(), 1)


if __name__ == '__main__':
    unittest.main()
