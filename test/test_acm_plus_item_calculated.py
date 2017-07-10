import unittest
from decimal import *

from nose.tools import eq_

from buoy.lib.device.currentmeter.acmplus import ACMPlusItem


class TestACMlusItem(unittest.TestCase):
    def test_calculate_properties(self):
        data = {
            'vx': -45.81,
            'vy': 152.0,
            'speed': 158.753,
            'direction': 343.228
        }

        item = ACMPlusItem(vx=data['vx'], vy=data['vy'])

        for key, value in data.items():
            eq_(round(getattr(item, key), 2), round(Decimal(value), 2))

    def test_calculate_properties_value_zero(self):
        data = {
            'vx': 0,
            'vy': 0.79,
            'speed': 0.79,
            'direction': 0
        }

        item = ACMPlusItem(vx=data['vx'], vy=data['vy'])

        for key, value in data.items():
            eq_(round(getattr(item, key), 2), round(Decimal(value), 2))

if __name__ == '__main__':
    unittest.main()
