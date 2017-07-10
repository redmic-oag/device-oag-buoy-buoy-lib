import unittest

import pynmea2
from nose.tools import eq_, ok_

from buoy.lib.protocol.item import DataEncoder
from buoy.lib.protocol.nmea0183 import WIMDA
from datetime import datetime, timezone
from decimal import Decimal
import json


class TestProtocolNMEA0183(unittest.TestCase):
    def setUp(self):
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

        self.item_expected = WIMDA(
            datetime=self.data['datetime'],
            barometric_pressure_inch=self.data['barometric_pressure_inch'],
            barometric_pressure_bar=self.data['barometric_pressure_bar'],
            air_temperature=self.data['air_temperature'],
            water_temperature=self.data['water_temperature'],
            relative_humidity=self.data['relative_humidity'],
            absolute_humidity=self.data['absolute_humidity'],
            dew_point=self.data['dew_point'],
            wind_direction_true=self.data['wind_direction_true'],
            wind_direction_magnetic=self.data['wind_direction_magnetic'],
            wind_speed_knots=self.data['wind_speed_knots'],
            wind_speed_meters=self.data['wind_speed_meters']
        )

    def test_wimda_properties(self):

        item = WIMDA(**self.data)

        for name in dir(item):
            value = getattr(item, name)
            if type(value) is datetime:
                eq_(True, True)
            elif type(value) is Decimal:
                eq_(value, Decimal(self.data[name]))
            else:
                eq_(value, self.data[name])

    def test_wimda_fulled(self):

        mda = pynmea2.MDA('WI', 'MDA', (
            self.data['barometric_pressure_inch'], 'I', self.data['barometric_pressure_bar'], 'B',
            self.data['air_temperature'], 'C', self.data['water_temperature'], 'C', self.data['relative_humidity'],
            self.data['absolute_humidity'], self.data['dew_point'], 'C', self.data['wind_direction_true'], 'T',
            self.data['wind_direction_magnetic'], 'M', self.data['wind_speed_knots'], 'N',
            self.data['wind_speed_meters'], 'M'))

        item = WIMDA.from_nmea(self.data['datetime'], mda)

        eq_(item, self.item_expected)

    def test_wimda_incompleted(self):
        del self.data['water_temperature']
        del self.data['relative_humidity']

        item = WIMDA(**self.data)

        ok_(not getattr(item, 'water_temperature'))
        ok_(not getattr(item, 'relative_humidity'))
        
    def test_wimda_serialize(self):
        serial = json.dumps(self.item_expected, cls=DataEncoder, sort_keys=True)

        testo = str(self.item_expected)

        json_expected = ('"absolute_humidity": {absolute_humidity}, '
                         '"air_temperature": {air_temperature}, '
                         '"barometric_pressure_bar": {barometric_pressure_bar}, '
                         '"barometric_pressure_inch": {barometric_pressure_inch}, '
                         '"datetime": "{datetime}", '
                         '"dew_point": {dew_point}, '
                         '"relative_humidity": {relative_humidity}, '
                         '"water_temperature": {water_temperature}, '
                         '"wind_direction_magnetic": {wind_direction_magnetic}, '
                         '"wind_direction_true": {wind_direction_true}, '
                         '"wind_speed_knots": {wind_speed_knots}, '
                         '"wind_speed_meters": {wind_speed_meters}').format(**dict(self.item_expected))

        ok_(json_expected in str(serial))

    def test_wimda_deserialize(self):
        json_in = ('{"id": 2, "absolute_humidity": 21.0, "air_temperature": 26.8, "barometric_pressure_bar": 1.027,'
                   '"barometric_pressure_inch": 30.3273, "datetime": "2017-02-14 12:46:32.584366", "dew_point": 2.3,'
                   '"relative_humidity": 12.3, "water_temperature": 20.1, "wind_direction_magnetic": 128.7, '
                   '"wind_direction_true": 2.0, "wind_speed_knots": 134.6, "wind_speed_meters": 0.3}')

        a = json.loads(json_in)

        item = WIMDA(**a)

        eq_(item.id, 2)
        eq_(item.wind_speed_knots, Decimal(134.6))

if __name__ == '__main__':
    unittest.main()

