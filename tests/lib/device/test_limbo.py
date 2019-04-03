import unittest

from nose.tools import eq_, ok_

from buoy.base.device.threads.mqtt import Limbo
from buoy.tests.item import *


class TestLimbo(unittest.TestCase):

    def test_itemAdded_when_callAddItemLimbo(self):
        limbo = Limbo()
        item = get_item()
        limbo.add(1, item)

        ok_(limbo.exists(1))
        eq_(limbo.size(), 1)

    def test_clearLimbo_when_addedItemsAndClearedLimbo(self):
        limbo = Limbo()

        items = get_items(2)
        for idx, item in enumerate(items):
            limbo.add(idx, item)

        eq_(limbo.size(), 2)
        limbo.clear()
        eq_(limbo.size(), 0)

    def test_returnItem_when_passId(self):
        limbo = Limbo()
        items = get_items(2)
        for idx, item in enumerate(items):
            limbo.add(idx, item)

        eq_(limbo.size(), 2)
        item = limbo.pop(1)
        ok_(item is not None)
        eq_(limbo.size(), 1)
        item = limbo.get(1)
        ok_(item is None)
