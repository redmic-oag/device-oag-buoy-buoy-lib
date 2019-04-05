import unittest
from datetime import datetime, timedelta
from unittest.mock import patch

from nose.tools import eq_

from buoy.base.data.item import BufferItems
from dateutil import parser
from buoy.base.data.utils import convert_to_seconds
from buoy.tests.item import Item, get_items, get_item


class TestData(unittest.TestCase):

    def test_shouldReturnNumberSeconds_when_passFewIntervals(self):
        check = [{"in": 1, "out": 1}, {"in": "1", "out": 1}, {"in": "1m", "out": 60}, {"in": "10m", "out": 600}]
        for item in check:
            sec = convert_to_seconds(item["in"])
            eq_(sec, item["out"])

    def test_shouldReturnStatusInOutInterval_when_passFewDates(self):
        buffer = BufferItems(interval="10m")
        date = datetime.strptime("2019-01-01T00:01:59", "%Y-%m-%dT%H:%M:%S")
        check = [{"in": "2019-01-01T00:00:00", "out": False}, {"in": "2019-01-01T00:05:00", "out": True},
                 {"in": "2019-01-01T00:10:10", "out": False}, {"in": "2019-01-01T00:10:00", "out": True}]

        buffer.set_limits(date=date)

        for item in check:
            date = datetime.strptime(item["in"], "%Y-%m-%dT%H:%M:%S")
            eq_(buffer.inside_interval(date=date), item["out"])

    def test_shouldReturnLimitLowerAndHigher_when_setLimit(self):
        buffer = BufferItems(interval="10m")
        date = parser.parse("2019-04-05 07:29:06.356357+00:00")
        limit_lower = parser.parse("2019-04-05T07:20:00.000+00:00")
        limit_higher = parser.parse("2019-04-05T07:30:00.000+00:00")

        buffer.set_limits(date)

        eq_((limit_lower, limit_higher,), buffer.limits())

    @unittest.skip
    @patch.object(BufferItems, 'process_buffer')
    def test_shouldThreeProcessCalled_when_passFewDates(self, mock_process_buffer):
        buffer = BufferItems(interval="1m")
        dates = []
        date = datetime.strptime("2019-01-01T00:01:01.000", '%Y-%m-%dT%H:%M:%S.%f')
        for i in range(0, 200, 10):
            dates.append(date + timedelta(seconds=i))

        items = get_items(num=len(dates), dates=dates)

        for item in items:
            buffer.append(item)

        eq_(mock_process_buffer.call_count, 3)

    def test_returnCalculatedItem_when_passFewItems(self):
        buffer = BufferItems(interval="1m")

        item_expected = Item(date=datetime.strptime("2019-01-01T00:02:00.000", '%Y-%m-%dT%H:%M:%S.%f'), value=20.0)

        item1 = Item(date=datetime.strptime("2019-01-01T00:01:01.000", '%Y-%m-%dT%H:%M:%S.%f'), value=10.0)
        item2 = Item(date=datetime.strptime("2019-01-01T00:01:03.000", '%Y-%m-%dT%H:%M:%S.%f'), value=20.0)
        item3 = Item(date=datetime.strptime("2019-01-01T00:01:50.000", '%Y-%m-%dT%H:%M:%S.%f'), value=30.0)
        item4 = Item(date=datetime.strptime("2019-01-01T00:02:00.001", '%Y-%m-%dT%H:%M:%S.%f'), value=0.0)
        items = [item1, item2, item3, item4]

        items_processed = []
        for i in items:
            item = buffer.append(i)
            if item:
                items_processed.append(item)

        eq_(len(items_processed), 1)
        item_processed = items_processed[0]

        eq_(getattr(item_processed, "date"), getattr(item_expected, "date"))
        eq_(getattr(item_processed, "value"), getattr(item_expected, "value"))

    def test_returnItemWithNoneValue_when_passFewItemsWithNoneValue(self):
        buffer = BufferItems(interval="1m")

        item_expected = Item(date=datetime.strptime("2019-01-01T00:02:00.000", '%Y-%m-%dT%H:%M:%S.%f'), value=None)

        item1 = Item(date=datetime.strptime("2019-01-01T00:01:01.000", '%Y-%m-%dT%H:%M:%S.%f'), value=None)
        item2 = Item(date=datetime.strptime("2019-01-01T00:01:03.000", '%Y-%m-%dT%H:%M:%S.%f'), value=None)
        item3 = Item(date=datetime.strptime("2019-01-01T00:01:50.000", '%Y-%m-%dT%H:%M:%S.%f'), value=None)
        item4 = Item(date=datetime.strptime("2019-01-01T00:02:00.001", '%Y-%m-%dT%H:%M:%S.%f'), value=None)
        items = [item1, item2, item3, item4]

        items_processed = []
        for i in items:
            item = buffer.append(i)
            if item:
                items_processed.append(item)

        eq_(len(items_processed), 1)
        item_processed = items_processed[0]

        eq_(getattr(item_processed, "date"), getattr(item_expected, "date"))
        eq_(getattr(item_processed, "value"), getattr(item_expected, "value"))

    def test_returnListWithFieldName_when_passIntance(self):
        item = get_item()
        fields = BufferItems.extract_fieldname_parameters(item)
        eq_(len(fields), 1)
        eq_(fields[0], "value")


if __name__ == '__main__':
    unittest.main()
